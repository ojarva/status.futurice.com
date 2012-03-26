import pingdom
import json
import datetime
import time
import os
import sys
import pickle

from pingdom_settings import *

class Pingdomrun:

    def __init__(self):
        self.connection = pingdom.PingdomConnection(PINGDOM_USERNAME, PINGDOM_PASSWORD, PINGDOM_APPKEY)

    def get_cache(self, what):
        if os.path.exists("cache/%s" % what):
            return pickle.loads(open("cache/%s" % what).read())
        return False

    def set_cache(self, what, data):
        open("cache/%s" % what, "w").write(pickle.dumps(data))

    def get_checks(self, **kwargs):
        if not kwargs.get("nocache", False):
            cached = self.get_cache("checks")
            if cached is not False:
                return cached
        checks = self.connection.get_all_checks()
        self.set_cache("checks", checks)
        return checks

    def get_averages(self, checkid, timefrom, timeto):
        keyname = "averages-%s-%s-%s" % (checkid, timefrom, timeto)
        cached = self.get_cache(keyname)
        if cached is not False:
            return cached
        averages = self.connection.get_check_averages(checkid, timefrom=timefrom, timeto=timeto)
        self.set_cache(keyname, averages)
        return averages

    def get_outages(self, checkid, timefrom, timeto):
        keyname = "outages-%s-%s-%s" % (checkid, timefrom, timeto)
        cached = self.get_cache(keyname)
        if cached is not False:
            return cached
        outages = self.connection.get_outages(checkid, timefrom=timefrom, timeto=timeto)
        self.set_cache(keyname, outages)
        return outages

    def run(self):
        checks = self.get_checks(nocache=True)

        today_night = time.mktime(datetime.date.today().timetuple())
        today_last = int(time.mktime(datetime.datetime.now().timetuple()) / 1000 ) * 1000
        days_timeranges = []

        for a in range(5, -1, -1):
            new_end_time = today_night - 86400 * a
            new_start_time = today_night - 86400 * (a + 1)
            days_timeranges.append((new_start_time, new_end_time, datetime.datetime.fromtimestamp(new_start_time).strftime("%d.%m.")))
	days_timeranges.append((today_night, today_last, datetime.datetime.fromtimestamp(today_last).strftime("%d.%m. %H:%M")))

        data = {"overall": 0, "outages_today": 0, "outages_week": 0, "networks": 0, "virtualization_platforms": 0, "websites": 0, "day_titles": days_timeranges, "uptime_per_day": [], "outages_per_day": []}
        cdata = {}

        up_per_day = [0,0,0,0,0,0,0]
        down_per_day = [0,0,0,0,0,0,0]
        outages_per_day = [0,0,0,0,0,0,0]
        uptime_total = 0
        downtime_total = 0
        CHECK_KEYWORDS=["status", "name", "type", "resolution", "lasterrortime", "lastresponsetime", "lasttesttime"]
        for check in checks:
            cdata[check.id] = {"data": {"down": 0, "up": 0}, "dates": [], "avgms": []}
            for keyword in CHECK_KEYWORDS:
                try:
                    cdata[check.id][keyword] = getattr(check, keyword)
                except AttributeError:
                    pass

            counter = 0
            for (timefrom, timeto, datename) in days_timeranges:
                averages = self.get_averages(check.id, timefrom, timeto)
                avgresponse = 0
                c = 0
                for item in averages["summary"]["responsetime"]['avgresponse']:
                    c += 1
                    avgresponse += item['avgresponse']
                if c > 0:
                     avgresponse = round(float(avgresponse) / c)
                cdata[check.id]["avgms"] += [avgresponse]
                cdata[check.id]["data"]["down"] += averages["summary"]["status"]["totaldown"]
                cdata[check.id]["data"]["up"] += averages["summary"]["status"]["totalup"]
                up_per_day[counter] += averages["summary"]["status"]["totalup"]
                down_per_day[counter] += averages["summary"]["status"]["totaldown"]
                if averages["summary"]["status"]["totalup"] == 0:
                    uptime = 0
                else:
                    uptime = round((float(averages["summary"]["status"]["totalup"]) - float(averages["summary"]["status"]["totaldown"])) / float(averages["summary"]["status"]["totalup"]), 6)
                cdata[check.id]["dates"].append({"down": averages["summary"]["status"]["totaldown"], "up": averages["summary"]["status"]["totalup"], "u": uptime})

                downtime_total += averages["summary"]["status"]["totaldown"]
                uptime_total += averages["summary"]["status"]["totalup"]
                for classkey in UPTIME_CLASSES:
                    if check.id in UPTIME_CLASSES[classkey]['id']:
                        UPTIME_CLASSES[classkey]['down'] += averages["summary"]["status"]["totaldown"]
                        UPTIME_CLASSES[classkey]['up'] += averages["summary"]["status"]["totalup"]


                outages = self.get_outages(check.id, timefrom, timeto)
                for item in outages['states']:
                    if item["status"] == "down":
                        if item["timefrom"] > today_night:
                             data["outages_today"] += 1
                        if item["timefrom"] > today_night-7*86400:
                             data["outages_week"] += 1
                        outages_per_day[counter] += 1
                counter += 1


        for item in UPTIME_CLASSES:
            if UPTIME_CLASSES[item]["up"] == 0:
                data[item] = 0
            else:
                data[item] = str(round(100 * (float(UPTIME_CLASSES[item]["up"]) - float(UPTIME_CLASSES[item]["down"])) / float(UPTIME_CLASSES[item]["up"]), 3))+"%"
        for item in cdata:
            if cdata[item]["data"]["up"] == 0:
                cdata[item]["data"]["u"] = 0
            else:
                cdata[item]["data"]["u"] = round((float(cdata[item]["data"]["up"]) - float(cdata[item]["data"]["down"])) / float(cdata[item]["data"]["up"]), 6)
            del cdata[item]["data"]["up"]
            del cdata[item]["data"]["down"]

        for i in range(0, len(up_per_day)):
            if up_per_day[i] == 0:
                t_uptime = 0
            else:
                t_uptime = str(round(100*(float(up_per_day[i]) - float(down_per_day[i])) / float(up_per_day[i]), 3))
            data["uptime_per_day"].append(t_uptime)
        data["overall"] = str(round(100*(float(uptime_total) - float(downtime_total)) / float(uptime_total), 3))+"%"
        data["timestamp"] = {"unix": time.time(), "human": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        data["outages_per_day"] = outages_per_day
        open("../services.json", "w").write(json.dumps({"overall": data, "per_service": cdata}))

def main():
    a = Pingdomrun()
    a.run()


if __name__ == '__main__':
    main()
