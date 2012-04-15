import hashlib
import redis
import json
import os

class Frontpage:
    def __init__(self):
        self.redis = redis.Redis(unix_socket_path="/home/redis/redis.sock")

    def get_data(self):
        ret = {}

        pipe = self.redis.pipeline(transaction=False)
        pipe = pipe.get("data:ittickets.json")
        pipe = pipe.get("data:services.json")
        pipe = pipe.get("data:sauna.json")
        (tickets_json, services_json, sauna_json) = map(json.loads, pipe.execute())

        ret["unique_7d"] = tickets_json["data"]["unique_manual_7d"]
        ret["services_up"] = services_json["overall"]["services_up"];
        ret["services_unknown"] = services_json["overall"]["services_unknown"];
        ret["services_down"] = services_json["overall"]["services_down"];
        ret["sauna_temperature"] = "%s%s" % (sauna_json["autofill"]["sauna_current"], "&deg;C")
        ret["sauna_trend"] = sauna_json["autofill"]["sauna_trend"]

        return ret

    def run(self):
        content = {"autofill": self.get_data()}

        lastmodified = max(os.path.getmtime(__file__), self.redis.get("data:services.json-mtime"), self.redis.get("data:ittickets.json-mtime"), self.redis.get("data:sauna.json-mtime"))

        frontpage_mtime = self.redis.get("data:frontpage.json-mtime")

        if lastmodified <= frontpage_mtime:
            self.redis.incr("stats:cache:frontpage:hit");
            self.redis.incr("stats:cache:hit");
            return


        pipe = self.redis.pipeline(transaction=False)
        pipe = pipe.incr("stats:cache:frontpage:miss")
        pipe = pipe.incr("stats:cache:miss")

        contente = json.dumps(content)
        hash = hashlib.sha1(contente).hexdigest()
        exptime = 3600 * 24 * 30
        rediskey = "data:frontpage.json"
        pipe = pipe.setex(rediskey, contente, exptime)
        pipe = pipe.setex("%s-mtime" % rediskey, lastmodified, exptime)
        pipe = pipe.setex("%s-hash" % rediskey, hash, exptime)
        pipe = pipe.publish("pubsub:%s" % rediskey, json.dumps({"hash": hash, "mtime": lastmodified}))
        pipe.execute()



def main():
    frontpage = Frontpage()
    frontpage.run()

if __name__ == '__main__':
    main()
