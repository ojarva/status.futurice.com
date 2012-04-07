import hashlib
import redis
import json
import os

class Frontpage:
    def __init__(self):
        self.redis = redis.Redis()

    def get_data(self):
        ret = {}
        tickets_json = json.loads(self.redis.get("data:ittickets.json"))
        ret["unique_7d"] = tickets_json["data"]["unique_manual_7d"]
        services_json = json.loads(self.redis.get("data:services.json"))
        ret["services_up"] = services_json["overall"]["services_up"];
        ret["services_unknown"] = services_json["overall"]["services_unknown"];
        ret["services_down"] = services_json["overall"]["services_down"];
        return ret

    def run(self):
        content = {"autofill": self.get_data()}

        lastmodified = max(os.path.getmtime(__file__), self.redis.get("data:services.json-mtime"), self.redis.get("data:ittickets.json-mtime"))

        frontpage_mtime = self.redis.get("data:frontpage.json-mtime")

        if lastmodified <= frontpage_mtime:
            self.redis.incr("stats:cache:frontpage:hit");
            self.redis.incr("stats:cache:hit");
            return
        self.redis.incr("stats:cache:frontpage:miss")
        self.redis.incr("stats:cache:miss")

        contente = json.dumps(content)
        hash = hashlib.sha1(contente).hexdigest()
        exptime = 3600 * 24 * 30;
        self.redis.setex("data:frontpage.json", contente, exptime)
        self.redis.setex("data:frontpage.json-mtime", lastmodified, exptime)
        self.redis.setex("data:frontpage.json-hash", hash, exptime)
        self.redis.publish("data:frontpage.json", json.dumps({"hash": hash, "mtime": lastmodified}))


def main():
    frontpage = Frontpage()
    frontpage.run()

if __name__ == '__main__':
    main()
