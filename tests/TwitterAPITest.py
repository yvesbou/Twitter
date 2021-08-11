import unittest
from twitter import TwitterAPI, TwitterUser
import json


class TwitterAPITest(unittest.TestCase, TwitterAPI):
    example_user_json = {'data': {'entities': {'url': {'urls': [{'start': 0, 'end': 23, 'url': 'https://t.co/dKqFKMFhvC', 'expanded_url': 'https://www.youtube.com/aliabdaal','display_url': 'youtube.com/aliabdaal'}]}, 'description': {'urls': [
        {'start': 100, 'end': 123, 'url': 'https://t.co/WNUElMBhFB', 'expanded_url': 'http://academy.aliabdaal.com','display_url': 'academy.aliabdaal.com'}], 'mentions': [{'start': 37, 'end': 51, 'username': 'noverthinking'}]}},'public_metrics': {'followers_count': 96936, 'following_count': 1150,
                                                     'tweet_count': 5461, 'listed_count': 837},'pinned_tweet_id': '1424407105503645704', 'id': '30436279','profile_image_url': 'https://pbs.twimg.com/profile_images/1157059189161619456/Ke7LQ7NO_normal.jpg','description': '👨\u200d⚕️ Doctor, 🧪 YouTuber, 🎙 Podcaster @noverthinking. I teach people how to be Part-Time YouTubers - https://t.co/WNUElMBhFB','verified': False, 'protected': False, 'name': 'Ali Abdaal', 'created_at': '2009-04-11T11:49:42.000Z','location': 'Cambridge, UK', 'url': 'https://t.co/dKqFKMFhvC','username': 'AliAbdaal'}}

    @staticmethod
    def getExampleData():
        f = open("../testdata/followers.json", 'r')
        response = json.load(f)
        f.close()
        return response

    def testFollowsToList(self):
        response = TwitterAPITest.getExampleData()
        user = TwitterUser.createFromDict(TwitterAPITest.example_user_json['data'])
        followers = self._followsToList(user=user, response=response)


if __name__ == '__main__':
    unittest.main()
