""" Loads user information from Twitter """

import twitter
import sys
import json

class TwitterInfo:
    """ Load user information and timeline from twitter 
        (unauthenticated) API """

    def __init__(self, username):
        self.username = username
        self.api = twitter.Api()

    def fetch(self):
        """ Fetch user information and save status, follower count 
            and timestamp of status """
        user = self.api.GetUser(self.username)
        json.dump({"status": user.status.GetText(), 
              "followers": user.GetFollowersCount(), 
              "status_ago": user.status.GetRelativeCreatedAt()}, 
              open("../twitter.json", "w"))

    def fetch_timeline(self):
        """ Fetch user timeline and save it to json encoded file """
        msg = self.api.GetUserTimeline(self.username)
        json.dump({"statuses": msg}, open("../twitter_statuses.json", "w"))

def main(username):
    """ Run twitter information """
    twitterinfo = TwitterInfo(username)
    twitterinfo.fetch()


if __name__ == '__main__':
    main(sys.argv[1])
