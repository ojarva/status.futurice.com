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
        self.filename = "../data/twitter.json"
        self.statusfilename = "../data/twitter_statuses.json"

    def fetch(self):
        """ Fetch user information and save status, follower count 
            and timestamp of status """
        user = self.api.GetUser(self.username)
        new_data = json.dumps({"status": user.status.GetText(), 
              "followers": user.GetFollowersCount(), 
              "status_ago": user.status.GetRelativeCreatedAt(),
              "timestamp": user.status.GetCreatedAtInSeconds()})
        try:
            old_data = open(self.filename).read()
        except IOError:
            old_data = ""
        if new_data != old_data:
            open(self.filename, "w").write(new_data)

    def fetch_timeline(self):
        """ Fetch user timeline and save it to json encoded file """
        msg = self.api.GetUserTimeline(self.username)
        new_data = json.dumps({"statuses": msg})
        old_data = open(self.statusfilename).read()
 
        if new_data != old_data:
            open(self.statusfilename, "w").write(new_data)

def main(username):
    """ Run twitter information """
    twitterinfo = TwitterInfo(username)
    twitterinfo.fetch()


if __name__ == '__main__':
    main(sys.argv[1])
