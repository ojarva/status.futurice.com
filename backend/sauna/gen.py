import hashlib
import time
import json
from eta import EtaCalculator
import rrdtool
import redis

class SaunaStats:
    def __init__(self, filename):
        self.filename = filename
        self.redis = redis.Redis(unix_socket_path="/home/redis/redis.sock")

    def run(self):
        def get_sauna_eta(target, items):
            cachesort = "cache:sauna:eta:%s" % target
            cached = self.redis.get(cachesort)
            if cached:
                return float(cached)
            cachekey = "cache:sauna:eta:%s:%s"  % (target, hashlib.md5(json.dumps(items)).hexdigest())
            cached = self.redis.get(cachekey)
            if cached:
                return float(cached)
            eta = EtaCalculator(target, items).calc()
            self.redis.setex(cachekey, eta, 120)
            self.redis.setex(cachesort, eta, 30)
            return eta

        items = self.redis.lrange("cache:latest_sauna", 0, 30)
        items = map(float, items)
        items.reverse()
        sauna_eta_temperatures = []
        for a in range(40, 80,5):
            sauna_eta_temperatures.append([a, get_sauna_eta(a, items)])
        etas = get_sauna_eta(70, items)
        etas_raw = etas
        if etas > 0 and etas < 3600:
            etas = round(float(etas) / 60)
        else:
            etas = None

        items.reverse()
        sauna_trend = ""
        if items[0] < 40 and items[10] < 40 and items[20] < 40:
            sauna_trend = "cold"
        elif items[0] > 65 and items[10] > 65 and items[20] > 65:
            sauna_trend = "hot"
        elif etas:
            sauna_trend = "warming"
        elif items[0] > 40 and items[0] > items[10] and items[10] > items[20]:
            sauna_trend = "warming"
        elif items[0] < items[10] and items[10] < items[20]:
            sauna_trend = "cooling"
        else:
            sauna_trend = "?"

        data = {"autofill": {"sauna_current": round(items[0], 1), "sauna_trend": sauna_trend}, "sauna_eta": etas, "sauna_eta_raw": etas_raw, "sauna_eta_temperatures": sauna_eta_temperatures }

        content = json.dumps(data)

        hash = hashlib.sha1(content).hexdigest()

        if hash == self.redis.get("data:sauna.json-hash"):
            self.redis.incr("stats:cache:sauna:hit")
            self.redis.incr("stats:cache:hit")
            return
        self.redis.incr("stats:cache:sauna:miss")
        self.redis.incr("stats:cache:miss")

        exptime = 3600 * 24 * 30

        mtime = time.time()
        self.redis.setex("data:sauna.json", content, exptime);
        self.redis.setex("data:sauna.json-mtime", mtime, exptime);
        self.redis.setex("data:sauna.json-hash", hash, exptime);

        self.redis.publish("pubsub:data:sauna.json", json.dumps({"hash": hash, "mtime": mtime}))

        self.redis.delete("cache:sauna.png");

def main(filename):
    saunastats = SaunaStats(filename)
    saunastats.run()

if __name__ == '__main__':
    main("/var/www/upload/sauna.rrd")
