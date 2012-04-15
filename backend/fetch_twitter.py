""" Loads user information from Twitter """

import twitter
import sys
import json
import time
import hashlib
import redis

class TwitterInfo:
    """ Load user information and timeline from twitter 
        (unauthenticated) API """

    def __init__(self, username):
        self.username = username
        self.api = twitter.Api()
        self.redis = redis.Redis(unix_socket_path="/home/redis/redis.sock")
        self.redis_key = "data:twitter:%s" % username
        self.pipe = self.redis.pipeline(transaction=False)

    def fetch(self):
        """ Fetch user information and save status, follower count 
            and timestamp of status """
        user = self.api.GetUser(self.username)
        self.pipe = self.pipe.incr("stats:api:twitter:request")
        self.pipe = self.pipe.incr("stats:api:request")
        new_data = json.dumps({"status": user.status.GetText(), 
              "followers": user.GetFollowersCount(), 
              "status_ago": user.status.GetRelativeCreatedAt(),
              "timestamp": user.status.GetCreatedAtInSeconds()})
        new_hash = hashlib.sha1(new_data).hexdigest() 
        old_hash = self.redis.get(self.redis_key+"-hash")
        if new_hash != old_hash:
            max_lifetime = 3600 * 24 * 30
            self.pipe = self.pipe.setex("data:twitter.json", new_data, max_lifetime)
            self.pipe = self.pipe.setex("data:twitter.json-mtime", time.time(), max_lifetime)
            self.pipe = self.pipe.setex("data:twitter.json-hash", new_hash, max_lifetime)

            self.pipe = self.pipe.setex(self.redis_key, new_data, max_lifetime)
            self.pipe = self.pipe.setex("%s-mtime" % self.redis_key, time.time(), max_lifetime)
            self.pipe = self.pipe.setex("%s-hash" % self.redis_key, new_hash, max_lifetime)

            self.pipe = self.pipe.publish("pubsub:data:twitter.json", json.dumps({"hash": new_hash, "mtime": time.time()}))

            self.pipe = self.pipe.incr("stats:cache:twitter:miss")
            self.pipe = self.pipe.incr("stats:cache:miss")
        else:
            self.pipe = self.pipe.incr("stats:cache:twitter:hit")
            self.pipe = self.pipe.incr("stats:cache:hit")
        self.pipe.execute()

def main(username):
    """ Run twitter information """
    twitterinfo = TwitterInfo(username)
    twitterinfo.fetch()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.stderr.write("Syntax: %s your_twitter_handle\n" % sys.argv[0])
        sys.stderr.write("For example\n%s futurice\n" % sys.argv[0]);
        sys.exit(1)
    main(sys.argv[1])
