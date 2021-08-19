import unittest
import twitter

import responses
from responses import GET
import re


URL = re.compile(r"https://api.twitter.com/2*")


class TwitterUserTest(unittest.TestCase):
    def setUp(self):
        """
        instantiate api and twitter user, since many functions need a user instance
        :return:
        """
        self.api = twitter.TwitterAPI('xxx')
        self.responses = responses.RequestsMock()
        self.responses.start()

        with open('../testdata/user_without_expansion.json', 'r') as f:
            data = f.read()
            f.close()

        self.responses.add(GET, url=URL, body=data)

        self.user = self.api.getUser(userName="AliAbdaal", withExpansion=False)

        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

    def tearDown(self):
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

    # todo: modify with responses
    @responses.activate
    def testConstructionHelperMethod(self):
        with open('../testdata/user_without_expansion.json', 'r') as f:
            data = f.read()
            f.close()
        responses.add(GET, url=URL, body=data)
        user = self.api.getUser(userId=30436279, withExpansion=False)
        self.assertEqual(1150, user.following_count)  # rename to friends_count
        self.assertEqual({}, user.friends)
        self.assertEqual(96936, user.followers_count)
        self.assertEqual({}, user.followers)
        self.assertEqual('30436279', user.id)  # id is a string
        self.assertEqual("Ali Abdaal", user.name)
        self.assertEqual("2009-04-11T11:49:42.000Z", user.created_at)
        self.assertEqual("👨\u200d⚕️ Doctor, 🧪 YouTuber, 🎙 Podcaster @noverthinking. I teach people how to be Part-Time YouTubers - https://t.co/WNUElMBhFB", user.description)
        self.assertEqual('https://t.co/dKqFKMFhvC', user.url)
        self.assertEqual('Cambridge, UK', user.location)
        self.assertEqual(5461, user.tweet_count)
        self.assertEqual('1424407105503645704', user.pinned_tweet_id)
        self.assertEqual('https://pbs.twimg.com/profile_images/1157059189161619456/Ke7LQ7NO_normal.jpg', user.profile_image_url)
        self.assertEqual(837, user.listed_count)
        self.assertEqual(False, user.protected)
        self.assertEqual(False, user.verified)
        self.assertEqual(None, user.withheld)
        self.assertEqual({'url': {'urls': [{'start': 0, 'end': 23, 'url': 'https://t.co/dKqFKMFhvC', 'expanded_url': 'https://www.youtube.com/aliabdaal', 'display_url': 'youtube.com/aliabdaal'}]}, 'description': {'urls': [{'start': 100, 'end': 123, 'url': 'https://t.co/WNUElMBhFB', 'expanded_url': 'http://academy.aliabdaal.com', 'display_url': 'academy.aliabdaal.com'}], 'mentions': [{'start': 37, 'end': 51, 'username': 'noverthinking'}]}}, user.entities)

    @responses.activate
    def testSaveSingleFriend(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open('../testdata/user_without_expansion.json', 'r') as f:
            data = f.read()
            f.close()

        self.responses.add(GET, url=URL, body=data)

        twin = self.api.getUser(userName="AliAbdaal", withExpansion=False)

        self.user.saveSingleFriend(friend=twin)
        self.assertEqual(self.user.username, self.user.friends[twin.id].username)

    @responses.activate
    def testSaveSingleFollower(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open('../testdata/user_without_expansion.json', 'r') as f:
            data = f.read()
            f.close()

        self.responses.add(GET, url=URL, body=data)

        twin = self.api.getUser(userName="AliAbdaal", withExpansion=False)

        self.user.saveSingleFollower(follower=twin)
        self.assertEqual(self.user.username, self.user.followers[twin.id].username)

    @responses.activate
    def testSaveFriends(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open('../testdata/friends_2pages1_2_w1000_without_expansion.json', 'r') as f:
            data = f.read()
            f.close()
        self.responses.add(GET, url=URL, body=data)
        friends = self.api.getFollowers(user=self.user, numPages=1, withExpansion=False)
        self.user.saveFriends(friends=friends)
        self.assertEqual(friends, self.user.friends)

    @responses.activate
    def testSaveFollowers(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open('../testdata/followers_1page_w1000_without_expansion.json', 'r') as f:
            data = f.read()
            f.close()
        self.responses.add(GET, url=URL, body=data)
        followers = self.api.getFollowers(user=self.user, numPages=1, withExpansion=False)
        self.user.saveFollowers(followers=followers)
        self.assertEqual(followers, self.user.followers)


if __name__ == '__main__':
    unittest.main()
