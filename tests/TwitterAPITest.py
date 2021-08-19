import twitter

import unittest
import responses
from responses import GET

import json
import re

URL = re.compile(r"https://api.twitter.com/2*")


class TwitterAPITest(unittest.TestCase):

    @responses.activate
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

    def testSetUpAPI(self):
        self.assertEqual('xxx', self.api._TwitterAPI__bearer_token)

    # getUser(self, userId=None, userName=None, userIds=None, userNames=None, withExpansion=True):
    @responses.activate
    def testGetUser_withoutExpansion_wUserId(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open('../testdata/user_without_expansion.json', 'r') as f:
            data = f.read()
            f.close()
        self.responses.add(GET, url=URL, body=data)
        user = self.api.getUser(userId=30436279, withExpansion=False)
        self.assertEqual(user.name, "Ali Abdaal")
        self.assertEqual(user.tweets, {})
        self.assertIsInstance(user, twitter.TwitterUser)

    @responses.activate
    def testGetUser_withoutExpansion(self):
        self.assertEqual(self.user.name, "Ali Abdaal")
        self.assertEqual(self.user.tweets, {})
        self.assertIsInstance(self.user, twitter.TwitterUser)

    @responses.activate
    def testGetUsers_withExpansion_wMultipleUserNames(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open('../testdata/multiple_users_with_expansion.json', 'r') as f:
            data = f.read()
            f.close()
        self.responses.add(GET, url=URL, body=data)
        users = self.api.getUsers(userNames=['AliAbdaal', 'boutellier_yves', 'michael_saylor'])
        self.assertEqual(users[1].username, 'boutellier_yves')

    @responses.activate
    def testGetUsers_withExpansion_wMultipleIds(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open('../testdata/multiple_users_with_expansion.json', 'r') as f:
            data = f.read()
            f.close()
        self.responses.add(GET, url=URL, body=data)
        users = self.api.getUsers(userIds=[30436279, 1380593146971762690, 244647486])
        self.assertEqual(users[0].username, 'AliAbdaal')

    @responses.activate
    def testGetUser_noArgument(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open('../testdata/multiple_users_with_expansion.json', 'r') as f:
            data = f.read()
            f.close()
        self.responses.add(GET, url=URL, body=data)
        self.assertRaises(twitter.APIError, self.api.getUser)

    @responses.activate
    def testGetUser_withExpansion(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open('../testdata/user_with_expansion.json', 'r') as f:
            data = f.read()
            f.close()
        self.responses.add(GET, url=URL, body=data)
        resp = self.api.getUser(userName="AliAbdaal", withExpansion=True)
        tweet = next(iter(resp.tweets.values()))  # just one entry
        self.assertIsInstance(tweet, twitter.Tweet)

    @responses.activate
    def testGetUser_withExpansion_missingTweet(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open('../testdata/user_with_expansion_missingTweet.json', 'r') as f:
            data = f.read()
            f.close()
        self.responses.add(GET, url=URL, body=data)
        resp = self.api.getUser(userName="boutellier_yves", withExpansion=True)
        self.assertEqual('boutellier_yves', resp.username)

    @responses.activate
    def testGetFollowers_1page_withoutExpansion(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open('../testdata/followers_1page_w1000_without_expansion.json', 'r') as f:
            data = f.read()
            f.close()
        self.responses.add(GET, url=URL, body=data)
        resp = self.api.getFollowers(user=self.user, numPages=1, withExpansion=False)
        follower = next(iter(resp.values()))
        self.assertEqual(len(resp), 1000)
        self.assertIsInstance(resp, dict)
        self.assertIsInstance(follower, twitter.TwitterUser)

    @responses.activate
    def testGetFollowers_2pages_withoutExpansion(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open('../testdata/followers_2pages1_2_w1000_without_expansion.json', 'r') as f:
            data_1st_page = f.read()
            f.close()
        with open('../testdata/followers_2pages2_2_w1000_without_expansion.json', 'r') as f:
            data_2nd_page = f.read()
            f.close()
        self.responses.add(GET, url=URL, body=data_1st_page)
        self.responses.add(GET, url=URL, body=data_2nd_page)
        resp = self.api.getFollowers(user=self.user, numPages=2, withExpansion=False)
        follower = next(iter(resp.values()))
        self.assertEqual(len(resp), 2000)
        self.assertEqual(follower.tweets, {})
        self.assertIsInstance(resp, dict)
        self.assertIsInstance(follower, twitter.TwitterUser)

    @responses.activate
    def testGetFollowers_1page_withExpansion(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open("../testdata/followers_1page_w1000_with_expansion.json", "r") as f:
            data = f.read()
            f.close()
        self.responses.add(GET, url=URL, body=data)
        resp = self.api.getFollowers(user=self.user, numPages=1, withExpansion=True)
        follower = resp["2919776594"]  # need example that has actually a pinned Tweet
        pinnedTweet = next(iter(follower.tweets.values()))
        self.assertEqual(1000, len(resp))
        self.assertIsInstance(resp, dict)
        self.assertIsInstance(pinnedTweet, twitter.Tweet)
        self.assertEqual(follower.id, pinnedTweet.author_id)

    @responses.activate
    def testsGetFollowers_2page_withExpansion(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open('../testdata/followers_2pages1_2_w1000_with_expansion.json', 'r') as f:
            data_1st_page = f.read()
            f.close()
        with open('../testdata/followers_2pages2_2_w1000_with_expansion.json', 'r') as f:
            data_2nd_page = f.read()
            f.close()
        self.responses.add(GET, url=URL, body=data_1st_page)
        self.responses.add(GET, url=URL, body=data_2nd_page)
        resp = self.api.getFollowers(user=self.user, numPages=2, withExpansion=True)
        follower = resp["2919776594"]  # need example that has actually a pinned Tweet
        pinnedTweet = next(iter(follower.tweets.values()))
        self.assertEqual(2000, len(resp))
        self.assertIsInstance(resp, dict)
        self.assertIsInstance(pinnedTweet, twitter.Tweet)
        self.assertEqual(follower.id, pinnedTweet.author_id)

    @responses.activate
    def testGetFriends_1page_withoutExpansion(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open('../testdata/friends_2pages1_2_w1000_without_expansion.json', 'r') as f:
            data = f.read()
            f.close()
        self.responses.add(GET, url=URL, body=data)
        resp = self.api.getFriends(user=self.user, numPages=1, withExpansion=False)
        friend = next(iter(resp.values()))
        self.assertEqual(len(resp), 1000)
        self.assertIsInstance(resp, dict)
        self.assertIsInstance(friend, twitter.TwitterUser)

    @responses.activate
    def testGetFriends_2pages_withoutExpansion(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open('../testdata/friends_2pages1_2_w1000_without_expansion.json', 'r') as f:
            data_1st_page = f.read()
            f.close()
        with open('../testdata/friends_2pages2_2_w1000_without_expansion.json', 'r') as f:
            data_2nd_page = f.read()
            f.close()
        self.responses.add(GET, url=URL, body=data_1st_page)
        self.responses.add(GET, url=URL, body=data_2nd_page)
        resp = self.api.getFriends(user=self.user, numPages=2, withExpansion=False)
        friend = next(iter(resp.values()))
        self.assertAlmostEqual(len(resp), self.user.getFriendsCount(), delta=5)
        self.assertEqual(friend.tweets, {})
        self.assertIsInstance(resp, dict)
        self.assertIsInstance(friend, twitter.TwitterUser)

    @responses.activate
    def testGetFriends_1page_withExpansion(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open("../testdata/friends_2pages1_2_w1000_with_expansion.json", "r") as f:
            data = f.read()
            f.close()
        self.responses.add(GET, url=URL, body=data)
        resp = self.api.getFriends(user=self.user, numPages=1, withExpansion=True)
        friend = resp["14372143"]  # need example that has actually a pinned Tweet
        pinnedTweet = next(iter(friend.tweets.values()))
        self.assertEqual(1000, len(resp))
        self.assertIsInstance(resp, dict)
        self.assertIsInstance(pinnedTweet, twitter.Tweet)
        self.assertEqual(friend.id, pinnedTweet.author_id)

    @responses.activate
    def testsGetFriends_2page_withExpansion(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        with open('../testdata/friends_2pages1_2_w1000_with_expansion.json', 'r') as f:
            data_1st_page = f.read()
            f.close()
        with open('../testdata/friends_2pages2_2_w1000_with_expansion.json', 'r') as f:
            data_2nd_page = f.read()
            f.close()
        self.responses.add(GET, url=URL, body=data_1st_page)
        self.responses.add(GET, url=URL, body=data_2nd_page)
        resp = self.api.getFriends(user=self.user, numPages=2, withExpansion=True)
        friend = resp["14372143"]  # need example that has actually a pinned Tweet
        pinnedTweet = next(iter(friend.tweets.values()))
        self.assertAlmostEqual(len(resp), self.user.getFriendsCount(), delta=5)
        self.assertIsInstance(resp, dict)
        self.assertIsInstance(pinnedTweet, twitter.Tweet)
        self.assertEqual(friend.id, pinnedTweet.author_id)


if __name__ == '__main__':
    unittest.main()
