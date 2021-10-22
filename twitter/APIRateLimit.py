import time
import datetime
from dateutil.relativedelta import relativedelta
import json
from tqdm import tqdm


# function that evals the function and updates the correct field below?


class APIRateLimit(object):
    """
    This class is used to have stored data on the standings of the request towards the different limits
    such that the different functions that interact with the different endpoints don't have to return additional data
    """
    def __init__(self, tweetCap, tweetCount, tweetCapResetDate):
        self.today = datetime.datetime.today()
        self.tweetCap = tweetCap
        self.progress = tqdm(total=self.tweetCap)

        try:
            # continue with the tweetCount at which the program last terminated
            with open('tweetCapLog.json', 'r') as f:
                self.tweetCapData = json.load(fp=f)
                mostRecentLog = self.tweetCapData['data'][-1]
                self.tweetCount = mostRecentLog['tweetCount']
                self.progress.update(self.tweetCount)
                self.tweetCapResetDate = datetime.datetime.strptime(mostRecentLog['ResetDate'], '%Y-%m-%d')
                if self.tweetCapResetDate < self.today:
                    self.progress = tqdm(total=self.tweetCap)  # reset progress bar
                    self.tweetCount = 0  # reset counter
                    self.tweetCapResetDate = self.tweetCapResetDate + relativedelta(months=1)  # new reset date
                f.close()
        except FileNotFoundError:
            if tweetCount is None and tweetCapResetDate is None:
                # write new tweetCap file with no user defined input,
                # just 30 days from now is the reset date and 0 tweets have been made with the dev account is assumed
                self.tweetCapResetDate = self.today + relativedelta(months=1)
                self.tweetCount = 0
                self.tweetCapData = {"data": [{"logDate": self.today.strftime('%Y-%m-%d'), "tweetCount": self.tweetCount,
                                     "ResetDate": self.tweetCapResetDate.strftime('%Y-%m-%d')}]}
            else:
                # write new tweetCap file with user specified reset date and tweet count
                # if the user already used the API and his account before using this application

                try:  # check for formatting
                    datetime.datetime.strptime(self.tweetCapResetDate, '%Y-%m-%d')
                except ValueError:
                    # don't accept any other format atm
                    print("Please specify tweetCapResetDate according to the format '%Y-%m-%d', so for example: '2021.01.30' ")
                if tweetCount is None:
                    self.tweetCount = 0
                else:
                    self.tweetCount = tweetCount
                if tweetCapResetDate is None:
                    self.tweetCapResetDate = self.today + relativedelta(months=1)
                else:
                    self.tweetCapResetDate = tweetCapResetDate
                    if self.tweetCapResetDate < self.today:
                        self.progress = tqdm(total=self.tweetCap)
                        self.tweetCount = 0
                        self.tweetCapResetDate = self.tweetCapResetDate + relativedelta(months=1)
                self.tweetCapData = {"data": [{"date": self.today.strftime('%Y-%m-%d'), "tweetCount": self.tweetCount,
                                     "ResetDate": self.tweetCapResetDate}]}

            f = open('tweetCapLog.json', 'w')
            json.dump(obj=self.tweetCapData, fp=f)
            f.close()

        self.remainingTweets = self.tweetCap - self.tweetCount

        self.RequestsLeft_GET_Tweets_SearchStream = 50  # number of connections to stream
        self.RequestsLeft_GET_Rules_RulesSearchStream = 450
        self.RequestsLeft_GET_Users_LikingUsers = 75  # 100 users per request (if so many exists)
        self.RequestsLeft_GET_Tweets_LikedTweets = 75  # 100 users per request (if so many exists)
        self.RequestsLeft_GET_Users_RetweetedBy = 75
        self.RequestsLeft_GET_Tweets_SampleStream = 50  # number of connections to stream
        self.RequestsLeft_GET_Tweets_SearchRecent = 450
        self.RequestsLeft_GET_Users_mentions = 450
        self.RequestsLeft_GET_Tweets_byUser = 1500
        self.RequestsLeft_GET_TweetCounts_recent = 300
        self.RequestsLeft_GET_Tweet_byId = 300
        self.RequestsLeft_GET_Tweets_byIds = 300
        self.RequestsLeft_GET_Users_Followers = 15  # get max 15 pages of 1000
        self.RequestsLeft_GET_Users_Friends = 15  # get max 15 pages of 1000
        self.RequestsLeft_GET_User_byId = 300
        self.RequestsLeft_GET_Users_byIds = 300
        self.RequestsLeft_GET_User_byName = 300
        self.RequestsLeft_GET_Users_byNames = 300
        self.RequestsLeft_Post_Add_Rules = 450
        self.RequestsLeft_Post_Delete_Rules = 450
        self.RequestsLeft_Get_Rules = 450

        self._startTime = time.time()
        self.ResetTime_GET_Tweets_SearchStream = self._startTime
        self.ResetTime_GET_Rules_RulesSearchStream = self._startTime
        self.ResetTime_GET_Users_LikingUsers = self._startTime
        self.ResetTime_GET_Tweets_LikedTweets = self._startTime
        self.ResetTime_GET_Users_RetweetedBy = self._startTime
        self.ResetTime_GET_Tweets_SampleStream = self._startTime
        self.ResetTime_GET_Tweets_SearchRecent = self._startTime
        self.ResetTime_GET_Users_mentions = self._startTime
        self.ResetTime_GET_Tweets_byUser = self._startTime
        self.ResetTime_GET_TweetCounts_recent = self._startTime
        self.ResetTime_GET_Tweet_byId = self._startTime
        self.ResetTime_GET_Tweets_byIds = self._startTime
        self.ResetTime_GET_Users_Followers = self._startTime
        self.ResetTime_GET_Users_Friends = self._startTime
        self.ResetTime_GET_User_byId = self._startTime
        self.ResetTime_GET_Users_byIds = self._startTime
        self.ResetTime_GET_User_byName = self._startTime
        self.ResetTime_GET_Users_byNames = self._startTime
        self.ResetTime_Post_Add_Rules = self._startTime
        self.ResetTime_Get_Delete_Rules = self._startTime
        self.ResetTime_Get_Rules = self._startTime

    def __del__(self):
        # write to tweetCap logging file
        self.today = datetime.datetime.today()  # doesn't need to be the same day as the program started
        newLog = {"logDate": self.today.strftime('%Y-%m-%d'), "tweetCount": self.tweetCount,
                  "ResetDate": self.tweetCapResetDate}
        self.tweetCapData['data'].append(newLog)

        f = open('tweetCapLog.json', 'w')
        json.dump(obj=self.tweetCapData, fp=f)
        f.close()

    def resetTime(self):
        self.today = datetime.datetime.today()
        if self.today < self.tweetCapResetDate:
            return
        self.progress = tqdm(total=self.tweetCap)
        self.tweetCount = 0
        self.tweetCapResetDate = self.tweetCapResetDate + relativedelta(months=1)

    def countTowardsTweetCap(self, numberOfTweetsRequested):
        self.resetTime()
        self.tweetCount += numberOfTweetsRequested
        self.progress.update(numberOfTweetsRequested)






