import inspect


class TwitterObject:
    def __init__(self):
        self.param_defaults = {}

    def __repr__(self):
        output = [(key, value) for key, value in self.param_defaults.items()]
        print(output)

    @classmethod
    def createFromJson(cls, data):
        created_instance = cls(**data)
        return created_instance

    def createFollower(self, follower):
        pass

    def createFriend(self, friend):
        pass


class TwitterUser2(TwitterObject):
    def __init__(self, **kwargs):
        super().__init__()
        self.created_at = None
        self.description = None
        self.entities = None
        self.id = None
        self.location = None
        self.name = None
        self.pinned_tweet_id = None
        self.profile_image_url = None
        self.protected = None
        self.followers_count = None
        self.following_count = None
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

    """    def __str__(self):
            output = []
            attributes = inspect.getmembers(self)
            attributes = [a for a in attributes if not (a[0].startswith('__') and a[0].endswith('__'))]
            print(attributes)
            return attributes"""

    def createUsersFromFriends(self, data):
        """
        takes a whole list of user data in json format and returns a list of twitter-user instances
        and the func adds the self directly as follower to the created users
        :param data: list of json formatted twitter user
        :return: list of twitter user instances
        """
        output = []
        # todo: goal is to have dictionaries of each friend and loop through them
        for friend in data:
            instance = self.createFromJson(friend)
            instance.createFollower(self)
            output.append(instance)
        self.friends.extend(output)
        return output

    def createUsersFromFollowers(self, data):
        output = []
        for follower in data:
            instance = self.createFromJson(follower)
            instance.createFriend(self)
            output.append(instance)
        self.followers.extend(output)
        return output

    def createFollower(self, follower):
        self.followers.append(follower)

    def createFriend(self, friend):
        self.friends.append(friend)

    @classmethod
    def createFromJson(cls, data):
        """
        Json format used to instantiate twitter user
        :param data: dictionary json that contains information about a user
        :return: instance of twitter user class
        """
        tmp = []
        for (key, value) in data.items():
            try:
                items = value.items()
            except (AttributeError, TypeError):
                pass  # ie. value not a dictionary
            else:  # no exception raised
                for (secLvlKey, value) in items:
                    tmp.append((secLvlKey, value))
        for secLvlKey, value in tmp:
            data[secLvlKey] = value
        return super().createFromJson(data)

    def getFollowersCount(self):
        return self.followers_count

    def getFriendsCount(self):
        return self.following_count


class TwitterUser(TwitterObject):
    def __init__(self, **kwargs):
        super().__init__()
        self.param_defaults = {
            "created_at": None,  # i['data']['created_at']
            "description": None,  # i['data']['description']
            "entities": None,  # i['data']['entities'] there is more to it, leave it for now (any url in the bio is mentioned)
            "id": None,  # i['data']['id']
            "location": None,  # i['data']['location']
            "name": None,  # i['data']['name']
            "pinned_tweet_id": None,  # i['data']['pinned_tweet_id']
            "profile_image_url": None,  # i['data']['profile_image_url']
            "protected": None,  # i['data']['protected']
            "followers_count": None,  # ['data']['public_metrics']['followers_count']
            "following_count": None,  # ['data']['public_metrics']['following_count']
            "tweet_count": None,  # ['data']['public_metrics']['tweet_count']
            "listed_count": None,  # ['data']['public_metrics']['listed_count']
            "url": None,  # i['data']['url']
            "username": None,  # i['data']['username']
            "verified": None,  # i['data']['verified']
            "withheld": None}  # haven't seen in ali abdaal response

        for (param, default) in self.param_defaults.items():
            setattr(self, param, kwargs.get(param, default))

    @classmethod
    def createFromJson(cls, data):
        data = data['data'].copy()
        tmp = []
        for (key, value) in data.items():
            try:
                items = value.items()
            except (AttributeError, TypeError):
                pass
                #print(f"{value} is not a dictionary")
            else:  # no exception raised
                #print(type(items))
                for (secLvlKey, value) in items:
                    tmp.append((secLvlKey, value))
        for secLvlKey, value in tmp:
            data[secLvlKey] = value
        return super().createFromJson(data)

    def getFollowersCount(self):
        return self.followers_count

    def getFriendsCount(self):
        return self.following_count





i = {'data': {
    'public_metrics': {'followers_count': 96260, 'following_count': 1146, 'tweet_count': 5452, 'listed_count': 833},
    'protected': False,
    'profile_image_url': 'https://pbs.twimg.com/profile_images/1157059189161619456/Ke7LQ7NO_normal.jpg',
    'id': '30436279', 'url': 'https://t.co/dKqFKMFhvC', 'created_at': '2009-04-11T11:49:42.000Z',
    'description': '👨\u200d⚕️ Doctor, 🧪 YouTuber, 🎙 Podcaster @noverthinking. I teach people how to be Part-Time YouTubers - https://t.co/WNUElMBhFB',
    'name': 'Ali Abdaal', 'entities': {'url': {'urls': [{'start': 0, 'end': 23, 'url': 'https://t.co/dKqFKMFhvC',
                                                         'expanded_url': 'https://www.youtube.com/aliabdaal',
                                                         'display_url': 'youtube.com/aliabdaal'}]}, 'description': {
        'urls': [{'start': 100, 'end': 123, 'url': 'https://t.co/WNUElMBhFB',
                  'expanded_url': 'http://academy.aliabdaal.com', 'display_url': 'academy.aliabdaal.com'}],
        'mentions': [{'start': 37, 'end': 51, 'username': 'noverthinking'}]}}, 'location': 'Cambridge, UK',
    'username': 'AliAbdaal', 'pinned_tweet_id': '1365367682619564038', 'verified': False}}

#a = TwitterUser2(i)
#b = TwitterUser(i)

#a.location
#b.location