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
        self.redis = redis.Redis()
        self.redis_key = "data:twitter:%s" % username

    def fetch(self):
        """ Fetch user information and save status, follower count 
            and timestamp of status """
        user = self.api.GetUser(self.username)
        self.redis.incr("stats:api:twitter:request")
        self.redis.incr("stats:api:request")
        new_data = json.dumps({"status": user.status.GetText(), 
              "followers": user.GetFollowersCount(), 
              "status_ago": user.status.GetRelativeCreatedAt(),
              "timestamp": user.status.GetCreatedAtInSeconds()})
        new_hash = hashlib.sha1(new_data).hexdigest() 
        old_hash = self.redis.get(self.redis_key+"-hash")
        if new_hash != old_hash:
            max_lifetime = 3600 * 24 * 30
            self.redis.setex("data:twitter.json", new_data, max_lifetime)
            self.redis.setex("data:twitter.json-mtime", time.time(), max_lifetime)
            self.redis.setex("data:twitter.json-hash", new_hash, max_lifetime)

            self.redis.setex(self.redis_key, new_data, max_lifetime)
            self.redis.setex("%s-mtime" % self.redis_key, time.time(), max_lifetime)
            self.redis.setex("%s-hash" % self.redis_key, new_hash, max_lifetime)
            self.redis.incr("stats:cache:twitter:miss")
            self.redis.incr("stats:cache:miss")
        else:
            self.redis.incr("stats:cache:twitter:hit")
            self.redis.incr("stats:cache:hit")
def main(username):
    """ Run twitter information """
    twitterinfo = TwitterInfo(username)
    twitterinfo.fetch()


if __name__ == '__main__':
    main(sys.argv[1])
