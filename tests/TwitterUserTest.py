import unittest
import twitter

import ast
import json


class TwitterUserTest(unittest.TestCase):
    example_user_json = {'data': {'entities': {'url': {'urls': [{'start': 0, 'end': 23, 'url': 'https://t.co/dKqFKMFhvC', 'expanded_url': 'https://www.youtube.com/aliabdaal', 'display_url': 'youtube.com/aliabdaal'}]}, 'description': {'urls': [{'start': 100, 'end': 123, 'url': 'https://t.co/WNUElMBhFB', 'expanded_url': 'http://academy.aliabdaal.com', 'display_url': 'academy.aliabdaal.com'}], 'mentions': [{'start': 37, 'end': 51, 'username': 'noverthinking'}]}}, \
     'public_metrics': {'followers_count': 96936, 'following_count': 1150, 'tweet_count': 5461, 'listed_count': 837}, 'pinned_tweet_id': '1424407105503645704', 'id': '30436279', 'profile_image_url': 'https://pbs.twimg.com/profile_images/1157059189161619456/Ke7LQ7NO_normal.jpg', 'description': '👨\u200d⚕️ Doctor, 🧪 YouTuber, 🎙 Podcaster @noverthinking. I teach people how to be Part-Time YouTubers - https://t.co/WNUElMBhFB', 'verified': False, 'protected': False,\
      'name': 'Ali Abdaal', 'created_at': '2009-04-11T11:49:42.000Z', 'location': 'Cambridge, UK', 'url': 'https://t.co/dKqFKMFhvC', 'username': 'AliAbdaal'}}

    @staticmethod
    def _getFollowers(user):
        """
        helper method to perform testSaveFollowers
        """
        f = open("../testdata/followers.json", 'r')
        followersList = json.load(f)
        f.close()
        followers = []
        for follower in followersList['data']:
            followerInstance = twitter.TwitterUser.createFromDict(dict(follower))
            followerInstance.saveSingleFollower(user)
            followers.append(followerInstance)
        return followers

    @staticmethod
    def _getFriends(user):
        """
        helper method to perform testSaveFriends
        """
        f = open("../testdata/friends.json", 'r')
        friendsList = json.load(f)
        f.close()
        friends = []
        for friend in friendsList['data']:
            friendInstance = twitter.TwitterUser.createFromDict(friend)
            friendInstance.saveSingleFollower(user)
            friends.append(friendInstance)
        return friends

    def testConstructionHelperMethod(self):
        twitterUser = twitter.TwitterUser.createFromDict(TwitterUserTest.example_user_json['data'])  # method is called  this way in api.getUser
        self.assertEqual(twitterUser.username, "AliAbdaal")
        self.assertEqual(twitterUser.following_count, 1150)  # rename to friends_count
        self.assertEqual(twitterUser.friends, [])
        self.assertEqual(twitterUser.followers_count, 96936)
        self.assertEqual(twitterUser.followers, [])
        self.assertEqual(twitterUser.id, '30436279')  # id is a string
        self.assertEqual(twitterUser.name, "Ali Abdaal")
        self.assertEqual(twitterUser.created_at, "2009-04-11T11:49:42.000Z")
        self.assertEqual(twitterUser.description, "👨\u200d⚕️ Doctor, 🧪 YouTuber, 🎙 Podcaster @noverthinking. I teach people how to be Part-Time YouTubers - https://t.co/WNUElMBhFB")
        self.assertEqual(twitterUser.url, 'https://t.co/dKqFKMFhvC')
        self.assertEqual(twitterUser.location, 'Cambridge, UK')
        self.assertEqual(twitterUser.tweet_count, 5461)
        self.assertEqual(twitterUser.pinned_tweet_id, '1424407105503645704')
        self.assertEqual(twitterUser.profile_image_url, 'https://pbs.twimg.com/profile_images/1157059189161619456/Ke7LQ7NO_normal.jpg')
        self.assertEqual(twitterUser.listed_count, 837)
        self.assertEqual(twitterUser.protected, False)
        self.assertEqual(twitterUser.verified, False)
        self.assertEqual(twitterUser.withheld, None)
        self.assertEqual(twitterUser.entities, {'url': {'urls': [{'start': 0, 'end': 23, 'url': 'https://t.co/dKqFKMFhvC', 'expanded_url': 'https://www.youtube.com/aliabdaal', 'display_url': 'youtube.com/aliabdaal'}]}, 'description': {'urls': [{'start': 100, 'end': 123, 'url': 'https://t.co/WNUElMBhFB', 'expanded_url': 'http://academy.aliabdaal.com', 'display_url': 'academy.aliabdaal.com'}], 'mentions': [{'start': 37, 'end': 51, 'username': 'noverthinking'}]}})  # should I test this one, I guess so

    def testSaveSingleFriend(self):
        twitterUser = twitter.TwitterUser.createFromDict(TwitterUserTest.example_user_json['data'])
        twitterUserTwin = twitter.TwitterUser.createFromDict(TwitterUserTest.example_user_json['data'])
        twitterUser.saveSingleFriend(twitterUserTwin)
        self.assertEqual(twitterUser.username, twitterUser.friends[0].username)

    def testSaveSingleFollower(self):
        twitterUser = twitter.TwitterUser.createFromDict(TwitterUserTest.example_user_json['data'])
        twitterUserTwin = twitter.TwitterUser.createFromDict(TwitterUserTest.example_user_json['data'])
        twitterUser.saveSingleFollower(twitterUserTwin)
        self.assertEqual(twitterUser.username, twitterUser.followers[0].username)

    def testSaveFriends(self):
        twitterUser = twitter.TwitterUser.createFromDict(TwitterUserTest.example_user_json['data'])
        friends = self._getFriends(twitterUser)
        twitterUser.saveFriends(friendsList=friends)
        self.assertEqual(friends, twitterUser.friends)

    def testSaveFollowers(self):
        twitterUser = twitter.TwitterUser.createFromDict(TwitterUserTest.example_user_json['data'])
        followers = self._getFollowers(twitterUser)
        twitterUser.saveFollowers(followersList=followers)
        self.assertEqual(followers, twitterUser.followers)


if __name__ == '__main__':
    unittest.main()
