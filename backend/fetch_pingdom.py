""" This script fetches statistics from Pingdom. Requires 
pingdom_settings.py with correct PINGDOM_USER, PINGDOM_PASSWORD, 
PINGDOM_APPKEY and UPTIME_CLASSES """

import pingdom
import json
import datetime
import time
import os
import logging
import redis
from dateutil import rrule

try:
    # cPickle is much faster than pickle
    import cPickle as pickle
except ImportError:
    import pickle

import pingdom_settings

class Pingdomrun:
    """ Fetch data from pingdom, calculate basic metrics like number of 
        outages, uptime percentages and save data as json """

    def __init__(self):
        self.uptime_classes = pingdom_settings.UPTIME_CLASSES
        self.connection = pingdom.PingdomConnection(
                          pingdom_settings.PINGDOM_USERNAME, 
                          pingdom_settings.PINGDOM_PASSWORD, 
                          pingdom_settings.PINGDOM_APPKEY)
        self.cache_directory = "cache/"
        self.data = None
        self.cdata = None
        self.redis = redis.Redis("localhost")

    def get_cache(self, what):
        """ Get pickled data from cache """
        value = self.redis.get(what)
        if not value:
            logging.debug("Cache miss: %s", what)
            return False
        logging.debug("Cache hit: %s", what)
        return pickle.loads(value)

    def set_cache(self, what, data, expire = None):
        """ Set (pickled) data to cache """
        status = self.redis.set(what, pickle.dumps(data))
        if status:
            logging.debug("Cache set: %s", what)
            if expire:
                self.redis.expire(what, expire)
        else:
            logging.debug("Cache set for %s failed", what)

    def get_performance(self, checkid, timefrom, timeto, resolution):
        keyname = "performance-%s-%s-%s-%s" % (checkid, timefrom, timeto, resolution)
        cached = self.get_cache(keyname)
        if cached is not False:
            return cached
        data = self.connection.get_performance(checkid, timefrom=timefrom, timeto=timeto, resolution=resolution)
        self.set_cache(keyname, data)
        return data

    def get_checks(self, **kwargs):
        """ Get list of checks and check details (status, last check 
          time, name etc.) """

        if not kwargs.get("nocache", False):
            cached = self.get_cache("checks")
            if cached is not False:
                logging.debug("Cache hit for checks")
                return cached
            logging.debug("Cache miss for checks")
        else:
            logging.debug("nocache was specified. Not checking cache")
        checks = self.connection.get_all_checks()
        self.set_cache("checks", checks)
        return checks

    def get_averages(self, checkid, timefrom, timeto, expire=None):
        """ Get averages for single check and single timeframe """
        keyname = "averages-%s-%s-%s" % (checkid, timefrom, timeto)
        if expire == None:
            if timefrom - timeto < 82000:
                expire = 86400
        cached = self.get_cache(keyname)
        if cached is not False:
            return cached
        averages = self.connection.get_check_averages(checkid, 
                               timefrom=timefrom, timeto=timeto)
        self.set_cache(keyname, averages, expire)
        logging.debug("Averages fetched for range %s-%s, check %s",
                             timefrom, timeto, checkid)
        return averages

    def get_outages(self, checkid, timefrom, timeto, expire=None):
        """ Get outages for single check """
        keyname = "outages-%s-%s-%s" % (checkid, timefrom, timeto)
        if expire == None:
            if timefrom - timeto < 82000:
                expire = 86400
        cached = self.get_cache(keyname)
        if cached is not False:
            return cached
        outages = self.connection.get_outages(checkid, 
                              timefrom=timefrom, timeto=timeto)
        self.set_cache(keyname, outages, expire)
        logging.debug("Outages fetched for range %s-%s, check %s",
                               timefrom, timeto, checkid)
        return outages

    @staticmethod
    def gen_daterange(today_night):
        """ Returns list of tuples containing start of day (unix 
            timestamp), end of day (unix timestamp) and human readable 
            name for day """
        today_last = int(time.mktime(datetime.datetime.now().timetuple()) / 1000 ) * 1000
        days_timeranges = []

        for day in range(5, -1, -1):
            new_end_time = today_night - 86400 * day
            new_start_time = today_night - 86400 * (day + 1)
            days_timeranges.append((new_start_time, new_end_time, datetime.datetime.fromtimestamp(new_start_time).strftime("%d.%m.")))
        days_timeranges.append((today_night, today_last, datetime.datetime.fromtimestamp(today_last).strftime("%d.%m. %H:%M")))
        return days_timeranges

    def populate_check_keywords(self, check):
        """ Populate cdata with basic check keywords - some might be 
            missing, for example if check never failed """
        check_keywords = ["status", "name", "type", "resolution", "lasterrortime", "lastresponsetime", "lasttesttime"]
        for keyword in check_keywords:
            try:
                self.cdata[check.id][keyword] = getattr(check, keyword)
            except AttributeError:
                pass

    def get_check_averages(self, check, timefrom, timeto, counter):
        """ Get averages and calculate necessary data """
        averages = self.get_averages(check.id, timefrom, timeto)
        avgresponse = 0
        avgcounter = 0
        for item in averages["summary"]["responsetime"]['avgresponse']:
            avgcounter += 1
            avgresponse += item['avgresponse']
        if avgcounter > 0:
            avgresponse = round(float(avgresponse) / avgcounter)
        self.cdata[check.id]["avgms"] += [avgresponse]
        self.cdata[check.id]["data"]["down"] += averages["summary"]["status"]["totaldown"]
        self.cdata[check.id]["data"]["up"] += averages["summary"]["status"]["totalup"]
        self.data["up_per_day"][counter] += averages["summary"]["status"]["totalup"]
        self.data["down_per_day"][counter] += averages["summary"]["status"]["totaldown"]
        if averages["summary"]["status"]["totalup"] == 0:
            uptime = 0
        else:
            uptime = min(1, round((float(averages["summary"]["status"]["totalup"]) - float(averages["summary"]["status"]["totaldown"])) / float(averages["summary"]["status"]["totalup"]), 6))
        self.cdata[check.id]["dates"].append({"down": averages["summary"]["status"]["totaldown"], "up": averages["summary"]["status"]["totalup"], "u": uptime})

        self.data["downtime_total"] += averages["summary"]["status"]["totaldown"]
        self.data["uptime_total"] += averages["summary"]["status"]["totalup"]
        for classkey in self.uptime_classes:
            if check.id in self.uptime_classes[classkey]['id']:
                self.uptime_classes[classkey]['down'] += averages["summary"]["status"]["totaldown"]
                self.uptime_classes[classkey]['up'] += averages["summary"]["status"]["totalup"]

    def get_check_outages(self, check, timefrom, timeto, today_night, counter):
        """ Get outages information for specific check """
        outages = self.get_outages(check.id, timefrom, timeto)
        for item in outages['states']:
            if item["status"] == "down":
                if item["timefrom"] > today_night:
                    self.data["autofill"]["outages_today"] += 1
                if item["timefrom"] > today_night-7*86400:
                    self.data["autofill"]["outages_week"] += 1
                self.data["outages_per_day"][counter] += 1



    def calculate_uptime_data(self):
        """ Calculate final statistics: uptime class values and per day 
            uptimes"""
        for item in self.uptime_classes:
            if self.uptime_classes[item]["up"] == 0:
                self.data["autofill"][item] = 0
            else:
                self.data["autofill"][item] = str(min(100, round(100 * (float(self.uptime_classes[item]["up"]) - float(self.uptime_classes[item]["down"])) / float(self.uptime_classes[item]["up"]), 3)))+"%"
        for item in self.cdata:
            if self.cdata[item]["data"]["up"] == 0:
                self.cdata[item]["data"]["u"] = 0
            else:
                self.cdata[item]["data"]["u"] = min(1, round((float(self.cdata[item]["data"]["up"]) - float(self.cdata[item]["data"]["down"])) / float(self.cdata[item]["data"]["up"]), 6))
            del self.cdata[item]["data"]["up"]
            del self.cdata[item]["data"]["down"]

        for i in range(0, len(self.data["up_per_day"])):
            if self.data["up_per_day"][i] == 0:
                t_uptime = 0
            else:
                t_uptime = str(min(100, round(100*(float(self.data["up_per_day"][i]) - float(self.data["down_per_day"][i])) / float(self.data["up_per_day"][i]), 3)))
            self.data["uptime_per_day"].append(t_uptime)
        self.data["autofill"]["overall"] = str(round(100*(float(self.data["uptime_total"]) - float(self.data["downtime_total"])) / float(self.data["uptime_total"]), 3))+"%"


    def run(self):
        """ Get all data. Run save() to save it """
        checks = self.get_checks(nocache=True)

        today_night = time.mktime(datetime.date.today().timetuple())
        days_timeranges = Pingdomrun.gen_daterange(today_night)

        self.cdata = {}
        self.data = {"autofill": {"overall": 0,
                                  "outages_today": 0,
                                  "outages_week": 0,
                                  "networks": 0,
                                  "virtualization_platforms": 0,
                                  "websites": 0},
                     "day_titles": days_timeranges,
                     "uptime_per_day": [],
                     "outages_per_day": [0, 0, 0, 0, 0, 0, 0],
                     "services_up": 0,
                     "services_down": 0,
                     "services_unknown": 0,
                     "up_per_day": [0, 0, 0, 0, 0, 0, 0],
                     "down_per_day": [0, 0, 0, 0, 0, 0, 0],
                     "uptime_total": 0,
                     "downtime_total": 0}

        today = datetime.date.today()
        monday = today - datetime.timedelta(days=today.weekday())
        begin = monday - datetime.timedelta(days=112)
       
        weeks = []
        for dt in rrule.rrule(rrule.WEEKLY, dtstart=begin, until=monday-datetime.timedelta(days=1)):
            week_sunday = dt + datetime.timedelta(days=7) - datetime.timedelta(seconds=1)
            weeks.append((dt, week_sunday))

        for check in checks:
            
            self.cdata[check.id] = {"data": {"down": 0, "up": 0},
                                    "dates": [],
                                    "avgms": []}

            self.populate_check_keywords(check)




            if check.status == "up":
                self.data["services_up"] += 1
            elif check.status == "down":
                self.data["services_down"] += 1
            else:
                self.data["services_unknown"] += 1

            counter = 0
            for (timefrom, timeto, _) in days_timeranges:
                self.get_check_averages(check, timefrom, timeto, counter)
                self.get_check_outages(check, timefrom, timeto, today_night, counter)
                counter += 1

            checkdetails = {"autofill": self.cdata[check.id]};
            checkdetails["per_day"] = []
            for (week_start, week_end) in weeks:
                details = self.get_performance(check.id, time.mktime(week_start.timetuple()), time.mktime(week_end.timetuple()), "day").content["summary"]
                for item in details.get("days"):
                    checkdetails["per_day"].append(item)
            self.save_check(check.id, checkdetails)

        self.calculate_uptime_data()

        self.data["timestamp"] = {"unix": time.time(), 
             "human": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    def save_check(self, checkid, checkdetails):
        new_data = json.dumps(checkdetails)
        filename = "../data/per-check-%s.json" % checkid
        try:
            old_data = open(filename).read()
        except IOError:
            old_data = None
        if new_data != old_data:
            open(filename, "w").write(new_data)

    def save(self):
        """ Save data to services.json """
        new_data = json.dumps({"autofill": self.data.get("autofill", {}), "overall": self.data, "per_service": self.cdata})
        filename = "../data/services.json"
        try:
            old_data = open(filename).read()
        except IOError:
            old_data = None
        if new_data != old_data:
            open(filename, "w").write(new_data)


def main():
    """ Run pingdom statistics """
    pingdomstats = Pingdomrun()
    pingdomstats.run()
    pingdomstats.save()

if __name__ == '__main__':
    main()
