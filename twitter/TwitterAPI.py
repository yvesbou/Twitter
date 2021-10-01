import requests
import math
import json
import time

from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

from twitter.TwitterEntities import TwitterUser, Tweet, Poll, Place, Media
import twitter.utils as utils

from twitter.Error import APIError


class TwitterAPI(object):
    def __init__(self, bearer_token):
        self.__bearer_token = bearer_token
        self._userFields = "created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,withheld"
        # promoted_metrics,organic_metrics,private_metrics currently not part of tweetFields
        self._tweetFields = "attachments,author_id,context_annotations,conversation_id,created_at,entities,geo,id,in_reply_to_user_id,lang,public_metrics,possibly_sensitive,referenced_tweets,reply_settings,source,text,withheld"
        # non_public_metrics,organic_metrics,promoted_metrics currently not part of mediaFields
        self._mediaFields = "duration_ms,height,media_key,preview_image_url,type,url,width,public_metrics,alt_text"
        self._placeFields = "contained_within,country,country_code,full_name,geo,id,name,place_type"
        self._pollFields = "duration_minutes,end_datetime,id,options,voting_status"

    @staticmethod
    def _bearerOauth(bearer_token):
        """
        method required for bearer authentication
        :return: header required for authorization
        """
        header = {"Authorization": f"Bearer {bearer_token}"}
        return header

    def _makeRequest(self, url_param, params=None):
        """
        see each function to know the number of allowed requests per 15 minutes
        carries out the actual request via API endpoint of twitter API v2 early release and the library requests
        :param url_param: specified by the function that carries out the request e.g. get_followers: id + "/" + "following"
        :param params: not mandatory, can be used to specify the response with more detailed information about certain aspects
        :return: result of request as a dictionary
        """
        if not params:
            params = ""
        response = requests.get(f"https://api.twitter.com/2/{url_param}",
                                headers=self._bearerOauth(self.__bearer_token), params=params)
        return response.json()

    def _getResponse(self, str_input, params):
        response = self._makeRequest(str_input, params)
        self._checkError(response=response)
        return response

    @staticmethod
    def _checkError(response):
        if 'errors' in response.keys() and 'data' not in response.keys():  # errors is always a key for pinned tweets that were not found
            raise APIError(response['errors'][0]['message'])

    def _createParamsFollows(self, firstPage=True, token=None, withExpansion=None,
                             entriesPerPage=1000):
        params = {"user.fields": self._userFields, "max_results": f"{entriesPerPage}",
                  "tweet.fields": self._tweetFields}

        if withExpansion:
            params["expansions"] = "pinned_tweet_id"

        if not firstPage:
            params['pagination_token'] = token

        return params

    def _getFollowersResponse(self, user, firstPage=True, token=None, withExpansion=None,
                              entriesPerPage=1000):
        str_input = "users/" + str(user.id) + "/" + "followers"
        params = self._createParamsFollows(firstPage=firstPage, token=token, withExpansion=withExpansion,
                                           entriesPerPage=entriesPerPage)
        response = self._getResponse(str_input=str_input, params=params)
        return response

    def _getFriendsResponse(self, user, firstPage=True, token=None, withExpansion=None,
                            entriesPerPage=1000):
        str_input = "users/" + str(user.id) + "/" + "following"
        params = self._createParamsFollows(firstPage=firstPage, token=token, withExpansion=withExpansion,
                                           entriesPerPage=entriesPerPage)
        response = self._getResponse(str_input=str_input, params=params)
        return response

    @staticmethod
    def _pinnedTweetsToDict(response):
        tweets = {}
        for pinnedTweet in response['includes']['tweets']:  # pinnedTweet is a dict
            author_id = pinnedTweet['author_id']
            tweets[author_id] = Tweet.createFromDict(pinnedTweet, pinned=True)  # keys are author id's easy to match
        return tweets

    @staticmethod
    def _followersToDict(user, response):
        followers = {}
        for follower in response['data']:
            followerInstance = TwitterUser.createFromDict(follower)
            followerInstance.saveSingleFriend(user)
            Id = follower['id']
            followers[Id] = followerInstance
        return followers

    @staticmethod
    def _friendsToDict(user, response):
        friends = {}
        for friend in response['data']:
            friendsInstance = TwitterUser.createFromDict(friend)
            friendsInstance.saveSingleFollower(user)
            Id = friend['id']
            friends[Id] = friendsInstance
        return friends

    @staticmethod
    def _matchFollowsWithPinnedTweets(follows, pinnedTweets):
        """
        both follows and pinnedTweets need to be dictionaries
        :param follows:
        :param pinnedTweets:
        :return:
        """
        # loop through pinnedTweets since not every user has pinned tweets
        for author_id, tweet in pinnedTweets.items():
            user = follows[author_id]
            user.tweets[tweet.id] = tweet

    def _matchFollowsWithPlaces(self):
        pass
        # is it even possible to obtain place data, with Follow lookup it's not possible place.fields
        # maybe with getTweet, but then it would be called _matchTweetWithPlaces

    @staticmethod
    def limit_follows(user, numPages=None, percentagePages=None, follower=False):
        """
        This function is active on an interim basis
        :return:
        """
        if not any([numPages, percentagePages]):
            raise APIError("Specify either numPages or percentagePages")

        if numPages:
            iterations = numPages
            if numPages > 15:
                raise APIError("Please restrict yourself, atm max 15 pages. Sorry for this inconvenience")
        else:
            if follower:
                maxPages = math.ceil(user.getFollowersCount() / 1000)
            else:
                maxPages = math.ceil(user.getFriendsCount() / 1000)
            if 100 > percentagePages > 0:
                iterations = (percentagePages * maxPages) / 100
                if iterations > 15:
                    maximalPercentage = math.floor((15 * 100) / maxPages)
                    APIError(
                        f"The provided percentage was too high, atm only 15 pages are requestable, please for this user at max {maximalPercentage}% or provide numPages=15. Sorry for this inconvenience")
            else:
                raise APIError(
                    "If providing percentage, please provide a value between 0 and 100%. Sorry for this inconvenience")
        return iterations

    def getFollowers(self, user, numPages=None, percentagePages=None, entriesPerPage=1000, withExpansion=True):
        """
        Basic Account v2 API: Follow look-up: 15 requests per 15 minutes
        This function requests followers from an account
        :param entriesPerPage:
        :param percentagePages:
        :param numPages:
        :param withExpansion: get pinned tweets of followers
        :param user: user instance from that followers should be obtained
        :return: dictionary of followers from user that was specified by input
        """
        iterations = self.limit_follows(user=user, numPages=numPages, percentagePages=percentagePages, follower=True)

        response = self._getFollowersResponse(user=user, withExpansion=withExpansion,
                                              entriesPerPage=entriesPerPage)
        followers = self._followersToDict(user=user, response=response)

        if withExpansion:
            pinnedTweets = self._pinnedTweetsToDict(response=response)
            self._matchFollowsWithPinnedTweets(follows=followers, pinnedTweets=pinnedTweets)

        for i in range(0, (iterations - 1)):
            if 'next_token' in response['meta'].keys():
                token = response['meta']['next_token']

                response = self._getFollowersResponse(user=user, firstPage=False, token=token,
                                                      withExpansion=withExpansion)
                followers_toMerge = self._followersToDict(user=user, response=response)

                if withExpansion:
                    pinnedTweets = self._pinnedTweetsToDict(response=response)
                    self._matchFollowsWithPinnedTweets(follows=followers_toMerge, pinnedTweets=pinnedTweets)

                followers = {**followers, **followers_toMerge}  # merge dict python > 3.5
            else:
                return followers
        return followers

    def getFriends(self, user, numPages=None, percentagePages=None, entriesPerPage=1000, withExpansion=True):
        """
        Basic Account v2 API: Follow look-up: 15 requests per 15 minutes
        This function requests friends from an account

        desired usage:
        userInstanceFriends = api.getFriends(userInstance)

        :param entriesPerPage:
        :param numPages:
        :param percentagePages:
        :param withExpansion: get pinned tweets of friends
        :param user: user instance from that friends should be obtained
        :return: list of friends from user that was specified by input
        """
        iterations = self.limit_follows(user=user, numPages=numPages, percentagePages=percentagePages, follower=False)

        response = self._getFriendsResponse(user=user, withExpansion=withExpansion,
                                            entriesPerPage=entriesPerPage)
        friends = self._friendsToDict(user, response)

        if withExpansion:
            pinnedTweets = self._pinnedTweetsToDict(response=response)
            self._matchFollowsWithPinnedTweets(follows=friends, pinnedTweets=pinnedTweets)

        for i in range(0, (iterations - 1)):
            if 'next_token' in response['meta'].keys():
                token = response['meta']['next_token']
                response = self._getFriendsResponse(user=user, firstPage=False, token=token,
                                                    withExpansion=withExpansion)
                friends_toMerge = self._friendsToDict(user=user, response=response)

                if withExpansion:
                    pinnedTweets = self._pinnedTweetsToDict(response=response)
                    self._matchFollowsWithPinnedTweets(follows=friends_toMerge, pinnedTweets=pinnedTweets)

                friends = {**friends, **friends_toMerge}  # merge dict python > 3.5
            else:
                return friends
        return friends

    def getTweetsByUsername(self, username):
        """
        !deprecated!
        Basic/Academic Account v2 API: Tweet lookup 300(aps)/900(user)
        after providing the username, the function returns the last xx tweets
        :param username: username of the twitter account you want to have the tweets from
        :return: last x tweets
        """
        str_input = "tweets/search/recent"
        params = {'query': f'(from:{username})'}
        response = self._makeRequest(str_input, params)
        return response['data']

    @staticmethod
    def _extractUsersFromResponse(response):
        """
        This method is used by getReTweeters and getUsers to obtain user and if requested their pinned tweets.
        For getLikingUsersOfTweet another function is used as there are more expansions allowed to the pinned tweet
        :param response:
        :return:
        """
        users = []
        tweets = {}
        if 'includes' in response.keys():
            for tweetDict in response['includes']['tweets']:
                tweet = Tweet.createFromDict(data=tweetDict, pinned=True)
                tweets[tweet.id] = tweet
        for userDict in response['data']:
            userInstance = TwitterUser.createFromDict(userDict)
            try:
                pinnedTweet = tweets[userInstance.pinned_tweet_id]
                userInstance.tweets[pinnedTweet.id] = pinnedTweet
            except KeyError:  # users that don't have a pinned tweet
                pass
            users.append(userInstance)
        return users

    def _getUserResponse(self, userId=None, userName=None, withExpansion=True):
        if not any([userId, userName]):
            raise APIError("Please provide id or Username")

        params = {"user.fields": self._userFields, "tweet.fields": self._tweetFields}

        if userId:
            str_input = f"users/{userId}"

        elif userName:
            str_input = f"users/by/username/{userName}"

        if withExpansion:
            params["expansions"] = "pinned_tweet_id"
        response = self._getResponse(str_input=str_input, params=params)

        return response

    def _getUsersResponse(self, userIds=None, userNames=None, withExpansion=True):
        if not any([userIds, userNames]):
            raise APIError("Please provide ids or Usernames")

        params = {"user.fields": self._userFields, "tweet.fields": self._tweetFields}
        if userIds:
            str_input = "users"
            params['ids'] = ','.join([str(id) for id in userIds])

        else:
            str_input = "users/by"
            params['usernames'] = ','.join([name for name in userNames])

        if withExpansion:
            params["expansions"] = "pinned_tweet_id"

        response = self._getResponse(str_input=str_input, params=params)

        return response

    def getUser(self, userId=None, userName=None, withExpansion=True):
        """
        Basic/Academic Account v2 API: user-lookup: 300(aps)/900(user) lookups requests per 15 minutes
        :param userId: user id of account to look-up
        :param userName: username of account to look-up
        :param withExpansion: request additional data objects that relate to the originally returned users (without using up additional requests)
        :return: user instance defined in class TwitterUser
        """
        response = self._getUserResponse(userId=userId, userName=userName, withExpansion=withExpansion)
        user = TwitterUser.createFromDict(
            response['data'])  # key needed to make method in TwitterUser working for other cases as well
        if 'includes' in response.keys():
            pinnedTweet = Tweet.createFromDict(data=response['includes']['tweets'][0], pinned=True)
            # user owns tweets, tweets own realLifeEntities
            user.tweets[pinnedTweet.id] = pinnedTweet
        return user

    def getUsers(self, userIds=None, userNames=None, withExpansion=True):
        """
        Basic/Academic Account v2 API: user-lookup: 300(aps)/900(user) lookups requests per 15 minutes
        :param userIds:
        :param userNames:
        :param withExpansion:
        :return: list of user instances
        """
        response = self._getUserResponse(userId=userIds, userName=userNames, withExpansion=withExpansion)
        users = self._extractUsersFromResponse(response=response)
        return users

    def getLikingUsersOfTweet(self, tweetId, withExpansion=True):
        """
        You will receive the most recent 100 users who liked the specified Tweet.

        App rate limit: 75 requests per 15-minute window
        User rate limit: 75 requests per 15-minute window

        :param tweetId: Tweet ID of the Tweet to request liking users of.
        :param withExpansion: if True, pinned Tweets of users who liked the specified tweet
        :return: users
        """
        str_input = f"tweets/{tweetId}/liking_users"

        params = {"tweet.fields": self._tweetFields, "user.fields": self._userFields, "media.fields": self._mediaFields,
                  "place.fields": self._placeFields, "poll.fields": self._pollFields}
        if withExpansion:
            params["expansions"] = "pinned_tweet_id"

        response = self._getResponse(str_input=str_input, params=params)

        users = self._extractUsersFromResponse(response=response)

        return users

    def getLikesOfUser(self, UserId):
        """
        Allows you to get information about a user’s liked Tweets.

        App rate limit: 75 requests per 15-minute window
        User rate limit: 75 requests per 15-minute window

        :param UserId:
        :return: tweets
        """

    def _getTweetResponse(self, tweetId=None, tweetIds=None, withExpansion=True):
        """
        This function creates responses for getTweet and getTweets
        :param tweetId:
        :param tweetIds:
        :param withExpansion:
        :return:
        """
        params = {"tweet.fields": self._tweetFields, "user.fields": self._userFields, "media.fields": self._mediaFields,
                  "place.fields": self._placeFields, "poll.fields": self._pollFields}
        if tweetId:
            str_input = f"tweets/{tweetId}"
        if tweetIds:
            str_input = "tweets"
            params['ids'] = ','.join([str(id) for id in tweetIds])
        if withExpansion:
            params["expansions"] = [
                    "author_id,attachments.poll_ids,attachments.media_keys,entities.mentions.username,geo.place_id,in_reply_to_user_id,referenced_tweets.id,referenced_tweets.id.author_id"]
        response = self._getResponse(str_input=str_input, params=params)
        return response

    @staticmethod
    def _getLinkage(tweet):
        """
        helper function for getTweet and getTweets
        in matchingExpansionObjectsWithTweet the author_id of linked tweets are needed
        such that their user instances can be linked with the tweet
        :param tweet:
        :return:
        """

        # "attachments": {"media_keys": ["7_1427157481478832130"]}
        # "referenced_tweets": [{"type": "replied_to", "id": "1426125234378264576"}]
        # "attachments": {"poll_ids": ["1199786642468413448"]}

        links = [tweet.author_id]  # for getTweets the expansion includes the author object, for UserTimeLine as well

        for user in tweet.mentions:
            links.append(user.id)

        try:
            refTweet_id = tweet.referenced_tweets[0]['id']
            # refTweet_type = tweet.referenced_tweets[0]['type']
            links.append(refTweet_id)
        except (IndexError, AttributeError, TypeError) as error:
            pass

        try:
            place_id = tweet.geo['place_id']
            links.append(place_id)
        except (AttributeError, IndexError, KeyError) as error:
            pass

        try:
            for key, value in tweet.attachments.items():
                if key == "media_keys":
                    media_key = value[0]
                    links.append(media_key)
                if key == "poll_ids":
                    poll_id = value[0]
                    links.append(poll_id)
        except (IndexError, AttributeError, TypeError) as error:
            pass

        return links

    def getTweet(self, tweetId=None, withExpansion=True):
        """

        :param tweetId:
        :param withExpansion:
        :return: a Tweet object
        """
        if not tweetId:
            raise APIError("Please provide TweetId")

        response = self._getTweetResponse(tweetId=tweetId, withExpansion=withExpansion)

        tweets_Output = {}

        self._handleTweetResponse(response, tweets_Output, withExpansion)

        return list(tweets_Output.values())[0]

    def getTweets(self, tweetIds=None, withExpansion=True):
        """
        :param tweetIds:
        :param withExpansion: get additional information about media, poll, location
        :return: a list of tweets
        """
        if not tweetIds:
            raise APIError("Please provide TweetIds")
        response = self._getTweetResponse(tweetId=tweetIds, withExpansion=withExpansion)
        tweets_Output = {}
        self._handleMultipleTweetResponse(response=response, tweets_Output=tweets_Output, withExpansion=withExpansion)
        return tweets_Output

    def getRecentTweetsFromSearch(self, searchQuery, withExpansion, entriesPerPage=100, since_id=None, until_id=None, start_time=None, end_time=None):
        """
        App rate limit: 450 requests per 15-minute window
        User rate limit: 180 requests per 15-minute window

        The recent search endpoint returns Tweets from the last seven days (by default) that match a search query.
        For example: params = {'query': '(from:twitterdev -is:retweet) OR #twitterdev'}
        To find out how to build rules check out:
        https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/integrate/build-a-rule

        The Tweets returned by this endpoint count towards the Project-level Tweet cap.
        :param entriesPerPage: possible range from 10 to 100
        :param end_time:
        :param start_time:
        :param until_id:
        :param since_id:
        :param searchQuery: a string that says which tweets should be included in the output
        :param withExpansion:
        :return:
        """
        params = {"query": searchQuery, "tweet.fields": self._tweetFields, "user.fields": self._userFields, "media.fields": self._mediaFields,
                  "place.fields": self._placeFields, "poll.fields": self._pollFields, "max_results": f"{entriesPerPage}"}
        str_input = "tweets/search/recent"

        if withExpansion:
            params["expansions"] = [
                "author_id,attachments.poll_ids,attachments.media_keys,entities.mentions.username,geo.place_id,in_reply_to_user_id,referenced_tweets.id,referenced_tweets.id.author_id"]

        # By default, a request will return Tweets from up to seven days ago if you do not one of since/until id, start/end time.
        self._timeFrameHandler(params=params, since_id=since_id, until_id=until_id, start_time=start_time, end_time=end_time)

        tweets_Output = {}

        # app rate limit
        iterations = 180

        self._creatingTweetObjectsFromMultipleResponsePages(str_input=str_input, tweets_Output=tweets_Output, withExpansion=withExpansion,
                                                            iterations=iterations, params=params)

        return tweets_Output

    def getRecentTweetCountsFromSearch(self, searchQuery, granularity='hour', since_id=None, until_id=None, start_time=None, end_time=None):
        """
        The recent Tweet counts endpoint returns count of Tweets from the last seven days that match a search query.

        App rate limit: 300 requests per 15-minute window

        :param searchQuery:
        :param granularity: granularity the counting is grouped either minute, hour, day
        :param since_id:
        :param until_id:
        :param start_time:
        :param end_time:
        :return: dictionary from response
        """
        params = {"query": searchQuery, "granularity": granularity}
        self._timeFrameHandler(params=params, since_id=since_id, until_id=until_id, start_time=start_time, end_time=end_time)
        str_input = "tweets/counts/recent"

        response = self._getResponse(str_input=str_input, params=params)

        return response

    def getLikedTweetsByUserId(self, userid):
        """
        !deprecated
        Basic/Academic Account v2 API: Tweet lookup 75(aps)/75(user)
        :param userid: of account you want to see the liked tweets
        :return: json format of response
        """
        str_input = f"users/{userid}/liked_tweets"
        response = self._makeRequest(str_input)
        return response

    def getReTweeter(self, tweetId=None, withExpansion=True):
        """
        This function returns list of twitter users that retweeted a tweet specified by tweetId
        :param withExpansion: requests pinnedTweets of the reTweeters and stores them in the user objects
        :param tweetId:
        :return:
        """
        if not tweetId:
            raise APIError("Please provide TweetId")

        params = {"tweet.fields": self._tweetFields, "user.fields": self._userFields}

        str_input = f"tweets/{tweetId}/retweeted_by"

        if withExpansion:
            params["expansions"] = "pinned_tweet_id"

        response = self._getResponse(str_input=str_input, params=params)

        users = self._extractUsersFromResponse(response=response)
        return users

    @staticmethod
    def _createExpansionObjects(response):
        ExpansionObjects = {}
        conversionDict = {'users': 'TwitterUser', 'media': 'Media', 'places': 'Place', 'polls': 'Poll', 'tweets': 'Tweet'}
        for key in response['includes'].keys():
            for twitterEntity in response['includes'][key]:  # users, media, geo, polls, tweets
                entity = conversionDict[key]
                twitterEntityInstance = eval(entity).createFromDict(twitterEntity)
                linkingKey = twitterEntityInstance.linkWithTweet()
                ExpansionObjects[linkingKey] = (twitterEntityInstance, key)
        return ExpansionObjects

    def _matchExpansionWithTweet(self, tweet, ExpansionObjects, tweets_Output):
        links = self._getLinkage(tweet=tweet)
        for link in links:
            try:
                expansionObject, key = ExpansionObjects[link]
            except KeyError:
                # only some tweets miss include information, idk the reason for that, maybe imprecision of Twitter API
                pass
            if not hasattr(tweet, key) or getattr(tweet, key) is None:
                setattr(tweet, key,
                        [])  # if a list of e.g media instances does not exist yet, create list with this instance
            getattr(tweet, key).append(expansionObject)
        tweets_Output[tweet.id] = tweet

    def _handleTweetResponse(self, response, tweets_Output, withExpansion):
        if withExpansion:
            ExpansionObjects = self._createExpansionObjects(response=response)
            tweetDict = response['data']
            tweet = Tweet.createFromDict(data=tweetDict)
            self._matchExpansionWithTweet(tweet=tweet, ExpansionObjects=ExpansionObjects, tweets_Output=tweets_Output)
        else:
            tweetDict = response['data']
            tweet = Tweet.createFromDict(data=tweetDict)
            tweets_Output[tweet.id] = tweet

    def _handleMultipleTweetResponse(self, response, tweets_Output, withExpansion):
        if withExpansion:
            ExpansionObjects = self._createExpansionObjects(response=response)
            for tweetDict in response['data']:
                tweet = Tweet.createFromDict(data=tweetDict)
                self._matchExpansionWithTweet(tweet=tweet, ExpansionObjects=ExpansionObjects, tweets_Output=tweets_Output)
        else:
            for tweetDict in response['data']:
                tweet = Tweet.createFromDict(data=tweetDict)
                tweets_Output[tweet.id] = tweet

    def _creatingTweetObjectsFromMultipleResponsePages(self, str_input, tweets_Output, withExpansion, iterations, params):
        response = self._getResponse(str_input=str_input, params=params)
        self._handleMultipleTweetResponse(response=response, tweets_Output=tweets_Output, withExpansion=withExpansion)

        for i in range(0, iterations - 1):
            if 'next_token' in response['meta'].keys():
                token = response['meta']['next_token']
                params['pagination_token'] = token
                response = self._getResponse(str_input=str_input, params=params)
                self._handleMultipleTweetResponse(response=response, tweets_Output=tweets_Output,
                                                  withExpansion=withExpansion)
            else:
                break

    @staticmethod
    def _timeFrameHandler(params, since_id, until_id, start_time, end_time):
        if since_id:
            params['since_id'] = since_id
        if until_id:
            params['until_id'] = until_id
        if start_time:
            if utils.datetime_valid(start_time):
                params['start_time'] = start_time
            # else raise sth?
        if end_time:
            if utils.datetime_valid(end_time):
                params['end_time'] = end_time
            # else raise sth?

    def _prepareParamsTimeline(self, withExpansion, entriesPerPage, excludeRetweet, excludeReplies, since_id, until_id, start_time, end_time):
        params = {"tweet.fields": self._tweetFields, "user.fields": self._userFields, "media.fields": self._mediaFields,
                  "place.fields": self._placeFields, "poll.fields": self._pollFields,
                  "max_results": f"{entriesPerPage}"}

        if withExpansion:
            params["expansions"] = [
                "author_id,attachments.poll_ids,attachments.media_keys,entities.mentions.username,geo.place_id,in_reply_to_user_id,referenced_tweets.id,referenced_tweets.id.author_id"]

        if not excludeRetweet and not excludeReplies:
            params['exclude'] = ['retweets,replies']
        elif not excludeRetweet and excludeReplies:
            params['exclude'] = 'replies'
        elif excludeRetweet and not excludeReplies:
            params['exclude'] = 'retweets'

        self._timeFrameHandler(params=params, since_id=since_id, until_id=until_id, start_time=start_time,
                               end_time=end_time)

        return params

    def _getTweetsFromTimeline(self, str_input, withExpansion, entriesPerPage, excludeRetweet, excludeReplies, since_id, until_id, end_time, start_time):
        """
        Helper function for getUserMentionTimeline and getUserTweetTimeline to prevent code duplication
        :param str_input:
        :param withExpansion:
        :param entriesPerPage:
        :param excludeRetweet:
        :param excludeReplies:
        :param since_id:
        :param until_id:
        :param end_time:
        :param start_time:
        :return:
        """
        iterations = int(3200 / entriesPerPage)

        params = self._prepareParamsTimeline(withExpansion=withExpansion, entriesPerPage=entriesPerPage,
                                             excludeRetweet=excludeRetweet, excludeReplies=excludeReplies,
                                             since_id=since_id, until_id=until_id, start_time=start_time,
                                             end_time=end_time)

        tweets_Output = {}

        self._creatingTweetObjectsFromMultipleResponsePages(str_input=str_input, tweets_Output=tweets_Output,
                                                            withExpansion=withExpansion, iterations=iterations,
                                                            params=params)
        return tweets_Output

    def getUserTweetTimeline(self, userId=None, userName=None, withExpansion=True, entriesPerPage=100, excludeRetweet=False, excludeReplies=False, since_id=None, until_id=None, end_time=None, start_time=None):
        """
        Only the 3200 most recent Tweets are available, ie. max 32 requests per user
        Returns Tweets composed by a single user, specified by the requested user ID.
        By default, the most recent ten Tweets are returned per request.
        Using pagination, the most recent 3,200 Tweets can be retrieved.
        :param: start_time: Minimum allowable time is 2010-11-06T00:00:01Z (Provide in ISO8601)
        :param: end_time: Minimum allowable time is 2010-11-06T00:00:01Z (Provide in ISO8601)
        :return: dictionary key = tweet_id
        """
        if not userId and not userName:
            raise APIError("Please provide userId or userName")

        if userId:
            str_input = f"users/{userId}/tweets"
        else:
            str_input = f"users/by/username/{userName}/tweets"

        tweets_Output = self._getTweetsFromTimeline(str_input=str_input, withExpansion=withExpansion,
                                                    entriesPerPage=entriesPerPage, excludeRetweet=excludeRetweet,
                                                    excludeReplies=excludeReplies, since_id=since_id, until_id=until_id,
                                                    end_time=end_time, start_time=start_time)

        return tweets_Output

    def getUserMentionTimeline(self, userId=None, userName=None, withExpansion=True, entriesPerPage=100, excludeRetweet=False, excludeReplies=False, since_id=None, until_id=None, end_time=None, start_time=None):
        """
        Returns Tweets mentioning a single user specified by the requested user ID.
        By default, the most recent ten Tweets are returned per request.
        Using pagination, up to the most recent 800 Tweets can be retrieved.
        Rate Limit: - App rate limit: 450 requests per 15-minute window
                    - User rate limit: 180 requests per 15-minute window
        :param start_time:
        :param end_time:
        :param until_id:
        :param since_id:
        :param excludeReplies:
        :param excludeRetweet:
        :param entriesPerPage:
        :param userId:
        :param userName:
        :param withExpansion:
        :return:
        """
        if not userId and not userName:
            raise APIError("Please provide userId or userName")

        if userId:
            str_input = f"users/{userId}/mentions"
        else:
            str_input = f"users/by/username/{userName}/mentions"

        tweets_Output = self._getTweetsFromTimeline(str_input=str_input, withExpansion=withExpansion,
                                                    entriesPerPage=entriesPerPage, excludeRetweet=excludeRetweet,
                                                    excludeReplies=excludeReplies, since_id=since_id, until_id=until_id,
                                                    end_time=end_time, start_time=start_time)
        return tweets_Output

    def _streamer(self, str_input, withExpansion, secondsActive, timeout):
        """
        Provides streaming logic and processing for filtered and sample stream
        :param str_input:
        :param withExpansion:
        :param secondsActive:
        :param timeout:
        :return:
        """
        params = {"tweet.fields": self._tweetFields, "user.fields": self._userFields, "media.fields": self._mediaFields,
                  "place.fields": self._placeFields, "poll.fields": self._pollFields}

        if withExpansion:
            params["expansions"] = [
                "author_id,attachments.poll_ids,attachments.media_keys,entities.mentions.username,geo.place_id,in_reply_to_user_id,referenced_tweets.id,referenced_tweets.id.author_id"]

        tweets_Output = {}

        start = time.time()
        while True:
            try:
                resp = requests.get(str_input, headers=self._bearerOauth(self.__bearer_token), params=params,
                                    stream=True, timeout=timeout)
                if resp.status_code == 200:
                    for line in resp.iter_lines():
                        try:
                            responseAsDict = json.loads(line)
                            self._handleTweetResponse(responseAsDict, tweets_Output, withExpansion)
                            duration = time.time() - start
                            if duration > secondsActive:
                                return tweets_Output
                        except json.decoder.JSONDecodeError as error:  # if an empty byte response occurs, no problem, continue
                            continue
                elif resp.status_code == 429:
                    print("Too many reconnects.")
                    duration = time.time() - start
                    TimeLeft = secondsActive - duration
                    if 0 > TimeLeft:
                        return tweets_Output
                    elif 0 < TimeLeft < 60:
                        return tweets_Output
                    else:
                        time.sleep(10)
                        continue
                else:
                    print("Unhandled status `{}` retrieved, exiting.".format(resp.status_code))
                    return tweets_Output
            except requests.exceptions.Timeout:
                pass  # we'll ignore timeout errors and reconnect
            except requests.exceptions.RequestException as e:
                print("Request exception `{}`, exiting".format(e))
                pass

    def getTweetsFromFilteredStream(self, withExpansion=True, secondsActive=600, timeout=10):
        """
        Streams Tweets in real-time based on a specific set of filter rules.
        App rate limit: 50 requests per 15-minute window
        :return:
        """

        str_input = "https://api.twitter.com/2/tweets/search/stream"

        return self._streamer(str_input=str_input, withExpansion=withExpansion, secondsActive=secondsActive, timeout=timeout)

    def getTweetsFromStreamWithThreading(self, withExpansion=True, secondsActive=600, timeout=10):
        """
        probably slower than without threading
        Streams Tweets in real-time based on a specific set of filter rules.
        App rate limit: 50 requests per 15-minute window
        :return:
        """
        params = {"tweet.fields": self._tweetFields, "user.fields": self._userFields, "media.fields": self._mediaFields,
                  "place.fields": self._placeFields, "poll.fields": self._pollFields}

        if withExpansion:
            params["expansions"] = [
                "author_id,attachments.poll_ids,attachments.media_keys,entities.mentions.username,geo.place_id,in_reply_to_user_id,referenced_tweets.id,referenced_tweets.id.author_id"]

        str_input = "https://api.twitter.com/2/tweets/search/stream"
        tweets_Output = {}

        start = time.time()
        while True:
            duration = time.time() - start
            if duration > secondsActive:
                return tweets_Output
            try:
                resp = requests.get(str_input, headers=self._bearerOauth(self.__bearer_token), params=params, stream=True, timeout=timeout)
                if resp.status_code == 200:
                    with ThreadPoolExecutor() as executor:
                        for line in resp.iter_lines():
                            try:
                                responseAsDict = json.loads(line)
                                executor.submit(self._handleTweetResponse, responseAsDict, tweets_Output, withExpansion)
                            except json.decoder.JSONDecodeError as error:  # if an empty byte response occurs, no problem, continue
                                continue
                elif resp.status_code == 429:
                    print("Too many reconnects.")
                    duration = time.time() - start
                    TimeLeft = secondsActive - duration
                    if 0 > TimeLeft:
                        return tweets_Output
                    elif 0 < TimeLeft < 60:
                        return tweets_Output
                    else:
                        time.sleep(10)
                        continue
                else:
                    print("Unhandled status `{}` retrieved, exiting.".format(resp.status_code))
                    return tweets_Output
            except requests.exceptions.Timeout:
                pass  # we'll ignore timeout errors and reconnect
            except requests.exceptions.RequestException as e:
                print("Request exception `{}`, exiting".format(e))
                pass

    def addRulesForFilteredStream(self, rule, ruleName):
        """
        Let's you add rules that are applied for filtered Tweet streaming
        :param rule: a string of what you want to stream
        :param ruleName: a string
        :return: confirmation data as a dictionary provided by the Twitter API
        """
        if type(rule) is not str or type(ruleName) is not str:
            raise Exception("Rule and ruleName must be strings")

        sample_rules = [{"value": rule, "tag": ruleName}]

        payload = {"add": sample_rules}

        response = requests.post(
            "https://api.twitter.com/2/tweets/search/stream/rules",
            headers=self._bearerOauth(self.__bearer_token),
            json=payload)

        return response.json()

    def deleteRulesForFilteredStream(self, ids):
        """
        delete rule by specifying the id or multiple ids
        :param ids: a list of ids in string format
        :return: dictionary with confirmation data provided by the Twitter API
        """
        payload = {"delete": {"ids": ids}}
        response = requests.post(
            "https://api.twitter.com/2/tweets/search/stream/rules",
            headers=self._bearerOauth(self.__bearer_token),
            json=payload)
        return response.json()

    def getRulesForFilteredStream(self):
        """
        A function that provides you with the rules that are currently applied for the filtered stream
        :return: dictionary with all rules currently applied for the filtered stream
        """
        response = requests.get("https://api.twitter.com/2/tweets/search/stream/rules", headers=self._bearerOauth(self.__bearer_token))
        return response.json()

    def deleteAllRulesForFilteredStream(self):
        """
        A function that let's you delete all your rules
        :return: confirmation in dictionary format of the json response by the Twitter API
        """
        rules = self.getRulesForFilteredStream()

        if rules is None or "data" not in rules:
            return None

        ids = list(map(lambda rule: rule["id"], rules["data"]))
        payload = {"delete": {"ids": ids}}
        response = requests.post(
            "https://api.twitter.com/2/tweets/search/stream/rules",
            headers=self._bearerOauth(self.__bearer_token),
            json=payload)

        return response.json()

    def getTweetsFromSampleStream(self, withExpansion=True, secondsActive=600, timeout=10):
        """
        Streams about 1% of all Tweets in real-time.
        App rate limit: 50 requests per 15-minute window

        :param withExpansion:
        :param secondsActive:
        :param timeout:
        :return:
        """

        str_input = "https://api.twitter.com/2/tweets/sample/stream"

        return self._streamer(str_input=str_input, withExpansion=withExpansion, secondsActive=secondsActive,
                              timeout=timeout)






