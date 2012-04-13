import hashlib
import time
import json
from eta import EtaCalculator
import rrdtool
import redis

class SaunaStats:
    def __init__(self, filename):
        self.filename = filename
        self.redis = redis.Redis()

    def run(self):
        items = self.redis.lrange("cache:latest_sauna", 0, 50)
        items = map(float, items)
        eta = EtaCalculator(68, items)
        etas = eta.calc()
        if etas > 0 and etas < 3600:
            etas = round(float(etas) / 60)
        else:
            etas = None

        sauna_trend = ""
        if items[0] < 40 and items[10] < 40 and items[20] < 40:
            sauna_trend = "cold"
        elif items[0] > 65 and items[10] > 65 and items[20] > 65:
            sauna_trend = "hot"
        elif etas:
            sauna_trend = "warming"
        elif items[0] < items[10] and items[10] < items[20]:
            sauna_trend = "cooling"
        else:
            sauna_trend = "?"

        data = {"autofill": {"sauna_current": round(items[0], 1), "sauna_trend": sauna_trend}, "sauna_eta": etas}

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
