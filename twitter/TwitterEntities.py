import inspect
import numpy as np

from twitter.RealWorldEntity import RealWorldEntity
import twitter.utils as utils


class TwitterEntity:
    """def __init__(self):
        self.param_defaults = {}

    def __repr__(self):
        output = [(key, value) for key, value in self.param_defaults.items()]
        print(output)"""

    @classmethod
    def createFromDict(cls, data):
        created_instance = cls(**data)
        return created_instance

    def createFollower(self, follower):
        pass

    def createFriend(self, friend):
        pass


class TwitterUser(TwitterEntity):
    def __init__(self, **kwargs):
        super().__init__()
        self.created_at = None
        self.description = None
        self.entities = None
        self.id = None
        self.location = None
        self.name = None
        self.pinned_tweet_id = None  # helps to retrieve pinned tweet object from tweet dict
        self.profile_image_url = None
        self.protected = None
        self.followers_count = None
        self.following_count = None
        self.tweets = {}  # todo: create a function that makes a list out of this dictionary?
        self.tweet_count = None
        self.listed_count = None
        self.url = None
        self.username = None
        self.verified = None
        self.withheld = None
        self.friends = {}
        self.followers = {}
        self.start = None
        self.end = None
        for (param, attribute) in kwargs.items():
            setattr(self, param, attribute)

    def __str__(self):
        """
        ! not ready !
        :return:
        """
        output = []
        attributes = inspect.getmembers(self)
        attributes = [a for a in attributes if not (a[0].startswith('__') and a[0].endswith('__'))]
        return str(attributes)

    def __createUsersFromFriends(self, data):
        """
        deprecated!
        takes a whole list of user data in json format and returns a list of twitter-user instances
        and the func adds the self directly as follower to the created users
        :param data: list of json formatted twitter user
        :return: list of twitter user instances
        """
        output = []
        # todo: goal is to have dictionaries of each friend and loop through them
        for friend in data:
            instance = self.createFromDict(friend)
            instance.createFollower(self)
            output.append(instance)
        self.friends.extend(output)
        return output

    def __createUsersFromFollowers(self, data):
        """
        deprecated!
        :param data:
        :return:
        """
        output = []
        for follower in data:
            instance = self.createFromDict(follower)
            instance.createFriend(self)
            output.append(instance)
        self.followers.extend(output)
        return output

    def saveFollowers(self, followers):
        """
        stores multiple followers for an user instance
        :param followers
        """
        self.followers = {**self.followers, **followers}

    def saveSingleFollower(self, follower):
        """
        stores single follower for an user instance
        :param follower:
        """
        self.followers[follower.id] = follower

    def saveFriends(self, friends):
        """
        stores multiple friends for an user instance
        :param friends
        """
        self.friends = {**self.friends, **friends}

    def saveSingleFriend(self, friend):
        """
        stores single friend for an user instance
        :param friend:
        """
        self.friends[friend.id] = friend

    @classmethod
    def createFromDict(cls, data):
        """
        Json derived dict used to instantiate twitter user, if from friend or follower lookup loop through json,
        and for user lookup json dictionary indexed with ['data'], such that multiple functions work with the same function
        instantiation of tweet if pinned happens via Tweet.createFromDict called by function in TwitterAPI
        :param data: dictionary that contains information about a user
        :return: instance of twitter user class
        """
        tmp = []
        instantiationData = {}
        for (key, value) in data.items():
            try:
                items = value.items()
            except (AttributeError, TypeError):
                if key == "description":
                    transformed_text = utils.encodeDecodeTwitterText(value)
                    instantiationData[key] = transformed_text
                else:
                    instantiationData[key] = value  # ie. value not a dictionary
            else:  # no exception raised
                for (secLvlKey, secLvlvalue) in items:
                    # entities is not in higher resolution in the fields
                    if key == 'entities':
                        instantiationData[key] = value  # for entities
                        continue
                    tmp.append((secLvlKey, secLvlvalue))
        for secLvlKey, value in tmp:
            instantiationData[secLvlKey] = value
        return cls(**instantiationData)

    @classmethod
    def createFromMention(cls, dictionary):
        return cls(**dictionary)

    def getFollowersCount(self):
        return self.followers_count

    def getFriendsCount(self):
        return self.following_count

    def linkWithTweet(self):
        """
        if User was part of multiple Tweet request
        :return:
        """
        return self.id

    def __saveTweet(self, tweet):
        """
        deprecated: obsolete to store originated tweet since this tweet stores this object
        saves the Tweet which the User posted
        :param tweet: Tweet Object
        """
        self.tweets[tweet.id] = tweet


class Tweet(TwitterEntity):
    def __init__(self, **kwargs):
        super().__init__()
        # part of tweet as expansion fields
        self.id = None
        self.conversation_id = None
        self.text = None
        self.author_id = None   # todo: make function that can look up user instance via author id (maybe in neo4j) ... wait
        self.lang = None  # language (2 or 3-letter abbreviation according to ISO 639-2)
        self.created_at = None
        self.source = None
        self.reply_settings = None
        self.possibly_sensitive = None
        self.reply_count = None
        self.retweet_count = None
        self.like_count = None
        self.quote_count = None
        self.pinned = False
        self.in_reply_to_user_id = None
        self.referenced_tweets = None
        self.tweets = []  # saving referenced tweet objects
        self.realWorldEntities = []
        self.attachments = None
        self.users = []  # todo: maybe discard, conflict between mentions and users, are both needed? mentions is with or without expansion filled,
        #                   todo: users only if with expansion - is mentions a subset of users?
        self.urls = []
        self.media = []
        self.geo = {}  # place_id is associated with a place
        self.poll = []
        self.hashtags = []
        self.mentions = []  # mentioned in tweet, not author itself
        for (param, attribute) in kwargs.items():
            setattr(self, param, attribute)

    @classmethod
    def createFromDict(cls, data, pinned=False):
        instantiationData = {}
        realWorldEntities = []
        tweetType = "Tweet"
        tweetTypes = {"Tweet": "Tweet", "replied_to": "TweetReply", "retweeted": "Retweet", "quoted": "QuotedRetweet"}

        if pinned:
            instantiationData['pinned'] = pinned

        for (key, value) in data.items():
            if key not in ['public_metrics', 'entities', 'context_annotations']:
                if key == "text":
                    transformed_text = utils.encodeDecodeTwitterText(value)
                    instantiationData[key] = transformed_text
                elif key == "referenced_tweets":
                    tweetType = tweetTypes[value[0]['type']]
                    instantiationData[key] = value
                else:
                    instantiationData[key] = value

            elif key == 'public_metrics':
                for subKey in value.keys():
                    instantiationData[subKey] = value[subKey]

            elif key == 'context_annotations':
                for realWorldEntityDict in value:
                    rwEntity = RealWorldEntity()
                    realWorldEntities.append(rwEntity.createFromDictContextAnnotations(realWorldEntityDict))

            elif key == 'entities':
                instantiationData['mentions'] = []
                instantiationData['realWorldEntities'] = []
                for subKey, listDict in value.items():  # possible keys: mentions, hashtags, annotations, urls
                    if subKey in ['urls', 'hashtags']:
                        instantiationData[subKey] = listDict
                        continue
                    for dictionary in listDict:  # possible keys: start, end, and some specific to each category (annotations, mentions)
                        if subKey == "mentions":
                            user = TwitterUser.createFromMention(dictionary)
                            instantiationData['mentions'].append(user)
                        elif subKey == "annotations":
                            rwEntity = RealWorldEntity()
                            for rwKey, rwValues in dictionary.items():
                                setattr(rwEntity, rwKey, rwValues)
                            instantiationData['realWorldEntities'].append(rwEntity)

        return eval(tweetType)(**instantiationData)

    def linkWithTweet(self):
        """
        if tweet was created from referenced tweet, id needed to link with origin tweet
        :return: id of this instance
        """
        return self.id

    def __saveTweet(self, tweet):
        """
        deprecated: obsolete to store originated tweet since this tweet stores this object
        from referenced tweets
        :param tweet: a referenced tweet
        """
        self.tweets.append(tweet)


class Retweet(Tweet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class TweetReply(Tweet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class QuotedRetweet(Tweet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Media(TwitterEntity):
    def __init__(self, **kwargs):
        super().__init__()
        self.type = None
        self.media_key = None
        self.height = None
        self.width = None
        self.url = None

        for (param, attribute) in kwargs.items():
            setattr(self, param, attribute)

    @classmethod
    def createFromDict(cls, data):
        return cls(**data)

    def linkWithTweet(self):
        """
        if Media was part of multiple Tweet request
        :return:
        """
        return self.media_key

    def __saveTweet(self, tweet):
        """
        deprecated: obsolete to store originated tweet since this tweet stores this object
        saves the Tweet to which the Media belongs to
        :param tweet: Tweet Object
        """
        self.tweet = tweet


class Poll(TwitterEntity):
    def __init__(self, **kwargs):
        super().__init__()
        self.end_datetime = None
        self.id = None
        self.voting_status = None
        self.duration_minutes = None
        self.options = None

        for (param, attribute) in kwargs.items():
            setattr(self, param, attribute)

    @classmethod
    def createFromDict(cls, data):
        instantiationData = {}
        for key, value in data.items():
            if key == "options":
                tmp = []
                for optionDict in value:
                    tmpString = optionDict['label']
                    newTmpString = utils.encodeDecodeTwitterText(tmpString)
                    optionDict['label'] = newTmpString
                    tmp.append(optionDict)
                instantiationData[key] = tmp
            else:
                instantiationData[key] = value
        return cls(**instantiationData)

    def linkWithTweet(self):
        """
        if Poll was part of multiple Tweet request
        :return:
        """
        return self.id

    def __saveTweet(self, tweet):
        """
        deprecated: obsolete to store originated tweet since this tweet stores this object
        saves the Tweet to which the Poll belongs to
        :param tweet: Tweet Object
        """
        self.tweet = tweet


class Place(TwitterEntity):
    def __init__(self, **kwargs):
        super().__init__()

        for (param, attribute) in kwargs.items():
            setattr(self, param, attribute)

    @classmethod
    def createFromDict(cls, data):
        return cls(**data)

    def linkWithTweet(self):
        """
        if Poll was part of multiple Tweet request
        :return:
        """
        try:
            return self.id
        except AttributeError:
            return None
