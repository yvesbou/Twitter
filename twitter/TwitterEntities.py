import inspect
import numpy as np

from twitter.RealWorldEntity import RealWorldEntity


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
        self.pinnedTweetId = None
        self.profile_image_url = None
        self.protected = None
        self.followers_count = None
        self.following_count = None
        self.tweets = []
        self.tweet_count = None
        self.listed_count = None
        self.url = None
        self.username = None
        self.verified = None
        self.withheld = None
        self.friends = []
        self.followers = []
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

    def createUsersFromFriends(self, data):
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

    def createUsersFromFollowers(self, data):
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

    def saveFollowers(self, followersList):
        """
        stores multiple followers for an user instance
        :param followersList: a list
        """
        self.followers.extend(followersList)

    def saveSingleFollower(self, follower):
        """
        stores single follower for an user instance
        :param follower:
        """
        self.followers.append(follower)

    def saveFriends(self, friendsList):
        """
        stores multiple friends for an user instance
        :param friendsList: a list
        """
        self.friends.extend(friendsList)

    def saveSingleFriend(self, friend):
        """
        stores single friend for an user instance
        :param friend:
        """
        self.friends.append(friend)

    @classmethod
    def createFromDict(cls, data):
        """
        Json derived dict used to instantiate twitter user, if from friend or follower lookup loop through json,
        and for user lookup json dictionary indexed with ['data'], such that multiple functions work with the same function
        :param data: dictionary that contains information about a user
        :return: instance of twitter user class
        """
        tmp = []
        instantiationData = {}
        for (key, value) in data.items():
            try:
                items = value.items()
            except (AttributeError, TypeError):
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

    def getFollowersCount(self):
        return self.followers_count

    def getFriendsCount(self):
        return self.following_count


class Tweet(TwitterEntity):
    def __init__(self, **kwargs):
        super().__init__()
        # part of tweet as expansion fields
        self.id = None
        self.conversation_id = None
        self.text = None
        self.author_id = None  # todo: make function that can look up user instance via author id (maybe in neo4j) ... wait
        self.lang = None
        self.created_at = None
        self.source = None
        self.reply_settings = None
        self.possibly_sensitive = None
        self.realWorldEntities = []
        self.reply_count = None
        self.retweet_count = None
        self.like_count = None
        self.quote_count = None
        self.media = []
        self.geo = []
        self.poll = None
        self.users = []  # mentioned in tweet, not author itself
        for (param, attribute) in kwargs.items():
            setattr(self, param, attribute)
        # part of tweet as non-expansion fields
        # ....

    @classmethod
    def createFromDict(cls, data):
        # todo: maybe the way tweets are instantiated from expansions is not the same as from direct request -> maybe create two functions
        instantiationData = {}
        realWorldEntities = []

        for (key, value) in data.items():
            if key not in ['public_metrics', 'entities', 'context_annotations']:
                instantiationData[key] = value

            if key == 'public_metrics':
                for subKey in value.keys():
                    instantiationData[subKey] = value[subKey]

        url = data['entities']['urls'][0]  # url dictionary, for tweet? entity?
        instantiationData['url'] = url

        # get real world entities from context annotations
        descriptionLookup = []
        for num, realWorldEntityDict in enumerate(data['context_annotations']):
            rwEntity = RealWorldEntity()
            for key in realWorldEntityDict['domain'].keys():
                domainKey = "domain"+key.capitalize()
                entityKey = "entity"+key.capitalize()
                setattr(rwEntity, domainKey, realWorldEntityDict['domain'][key])
                try:
                    setattr(rwEntity, entityKey, realWorldEntityDict['entity'][key])  # sometimes description is not a valid key for the entity dict
                except KeyError:
                    realWorldEntityDict['entity'][key] = "no description"
                    setattr(rwEntity, entityKey, realWorldEntityDict['entity'][key])

                if key == 'description':
                    description = realWorldEntityDict['entity'][key].split()
                    descriptionLookup.append((num, description))

            rwEntity.url = url
            realWorldEntities.append(rwEntity)

        for realWorldEntityDict in data['entities']['annotations']:
            rwEntity = RealWorldEntity()
            rwEntity.entityName = realWorldEntityDict['normalized_text']
            rwEntity.probability = realWorldEntityDict['probability']
            rwEntity.start = realWorldEntityDict['start']
            rwEntity.end = realWorldEntityDict['end']
            rwEntity.domainName = realWorldEntityDict['type']
            rwEntity.url = url
            realWorldEntities.append(rwEntity)

        instantiationData['realWorldEntities'] = realWorldEntities

        return cls(**instantiationData)


class Media(TwitterEntity):
    def __init__(self):
        super().__init__()

    def createFromDict(cls, data):
        pass


class Poll(TwitterEntity):
    def __init__(self):
        super().__init__()

    def createFromDict(cls, data):
        pass


class Place(TwitterEntity):
    def __init__(self):
        super().__init__()

    def createFromDict(cls, data):
        pass
