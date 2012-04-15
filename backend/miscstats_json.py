import json
import time
import redis
import hashlib
import os
import subprocess

class Miscstats:
    def __init__(self):
        self.redis = redis.Redis()

    def get_uptime(self):
        uptime = open("/proc/uptime").read().strip()
        uptime = uptime.split()
        uptime_original = round(float(uptime[0]))

        if uptime_original > 86400:
            uptime = "%s days" % round(uptime_original / 86400, 1)
        elif uptime_original > 3600:
            uptime = "%s hours" % round(uptime_original / 3600, 1)
        else:
            uptime = "%s minutes" % round(uptime_original / 60)

        return {"stats:server:uptime": uptime_original, "stats:server:uptime:readable": uptime}

    def get_redis_info(self):
        ret = {}
        for k, v in self.redis.info().items():
            ret["stats:redis:%s" % k] = v
        return ret

    def get_load_avg(self):
        content = open("/proc/loadavg").read().strip()
        content = content.split(" ")
        return {"stats:server:load:1m": content[0], "stats:server:load:5m": content[1], "stats:server:load:15m": content[2]}

    def get_traffic(self):
        def sizeof_fmt(num):
            for x in ['bytes','KB','MB','GB']:
                if num < 1024.0:
                    return "%3.1f%s" % (num, x)
                num /= 1024.0
            return "%3.1f%s" % (num, 'TB')

        p = subprocess.Popen(["/sbin/ifconfig", "eth0"], stdout=subprocess.PIPE)
        (content, _) = p.communicate()
        content = content.split("\n")
        for line in content:
            if "RX bytes" in line and "TX bytes" in line:
                line = line.strip().split("  ")
                sum = int(line[0].split(":")[1].split(" ")[0])
                sum += int(line[1].split(":")[1].split(" ")[0])
                return {"stats:server:net:eth0:total": sum, "stats:server:net:eth0:total:readable": sizeof_fmt(sum)}


    def update_graphs(self, final_values):
        for key, value in final_values.items():
            try:
                value = float(value)
            except ValueError, TypeError:
                continue
            v = int(round(value * 100))
            filename = "../data/miscstats_graphs/%s.rrd" % key
            if not os.path.exists(filename):
                p = subprocess.Popen(["rrdtool", "create", filename, "--step", "60", "--", "DS:valueg:GAUGE:300:U:U", "DS:valuec:COUNTER:300:U:U",
                    "RRA:AVERAGE:0.5:1:120", "RRA:AVERAGE:0.5:5:8640", "RRA:AVERAGE:0.5:60:4320", "RRA:AVERAGE:0.5:720:1600", "RRA:AVERAGE:0.5:1440:2000",
                    "RRA:MIN:0.5:1:120", "RRA:MIN:0.5:5:8640", "RRA:MIN:0.5:60:4320", "RRA:MIN:0.5:720:1600", "RRA:MIN:0.5:1440:2000",
                    "RRA:MAX:0.5:1:120", "RRA:MAX:0.5:5:8640", "RRA:MAX:0.5:60:4320", "RRA:MAX:0.5:720:1600", "RRA:MAX:0.5:1440:2000",
                    "RRA:LAST:0.5:1:120", "RRA:LAST:0.5:5:8640", "RRA:LAST:0.5:60:4320", "RRA:LAST:0.5:720:1600", "RRA:LAST:0.5:1440:2000"])
                p.wait()
            p = subprocess.Popen(["rrdtool", "update", filename, "N:%s:%s" % (v, v)])
            p.wait()

    def run(self):

        def format_key(keyname):
            return keyname.replace(":", "_")

        def format_value(value):
            try:
                value = float(value)
                if value.is_integer():
                    value = int(value)
                
            except:
                pass
            return value

        set_values = {}
        set_values.update(self.get_uptime())
        set_values.update(self.get_redis_info())
        set_values.update(self.get_load_avg())
        set_values.update(self.get_traffic())

        pipe = self.redis.pipeline(transaction=False)

        for key in set_values:
            pipe = pipe.sadd("temp:keystore:stats", key)
            value = self.redis.get(key)
            try:
                if float(value) < float(set_values.get(key)):
                    pipe = pipe.setex("%s:alltime" % key, set_values.get(key), 3600 * 24 * 30)
            except ValueError:
                pass

        pipe = pipe.mset(set_values)
        pipe = pipe.rename("temp:keystore:stats", "keystore:stats")
        pipe.execute()


        keys = self.redis.keys("stats:*")
        values = self.redis.mget(keys)
        values_done = map(format_value, values)
        keys_done = map(format_key, keys)
        final_values = dict(zip(keys_done, values_done))

        content = json.dumps({"autofill": final_values})

        hash = hashlib.sha1(content).hexdigest()
        if hash == self.redis.get("data:miscstats.json-hash"):
            pipe = pipe.incr("stats:cache:miscstats:hit")
            pipe = pipe.incr("stats:cache:hit")
            pipe.execute()
            return

        pipe = pipe.incr("stats:cache:miscstats:miss")
        pipe = pipe.incr("stats:cache:miss")

        exptime = 3600 * 24 * 30
        mtime = time.time()

        pipe = pipe.setex("data:miscstats.json", content, exptime);
        pipe = pipe.setex("data:miscstats.json-mtime", mtime, exptime);
        pipe = pipe.setex("data:miscstats.json-hash", hash, exptime);

        pipe = pipe.publish("pubsub:data:miscstats.json", json.dumps({"hash": hash, "mtime": mtime}))
        pipe.execute()

        self.update_graphs(final_values)

def main():
    miscstats = Miscstats()
    miscstats.run()

if __name__ == '__main__':
    main()
