import requests
import math
import time

from twitter.TwitterUser import TwitterUser

from twitter.Error import APIError


class TwitterAPI(object):
    def __init__(self, bearer_token):
        self.__bearer_token = bearer_token
        self._userFields = "created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,withheld"

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
        :return: result of request
        """
        if not params:
            params = ""
        response = requests.get(f"https://api.twitter.com/2/{url_param}", headers=self._bearerOauth(self.__bearer_token), params=params)
        # print(response)
        return response.json()

    def _getFollowsResponse(self, user, Friends=True, firstPage=True, token=None):
        """
        utility function for getFriends and getFollowers
        :param user: user from which friends or followers should be obtained
        :param Friends: specifies if Friends or Followers should be returned
        :param firstPage: specifies whether it's the first page of the request
        :param token: used to specify which page if not first page
        :return: response in json format passed to getFriends or getFollowers
        """
        if Friends:
            str_input = "users/" + str(user.id) + "/" + "following"
        else:
            str_input = "users/" + str(user.id) + "/" + "followers"

        params = {'user.fields': self._userFields, 'max_results': '1000'}
        if not firstPage:
            params['pagination_token'] = token

        response = self._makeRequest(str_input, params)
        if 'errors' in response.keys():
            raise APIError(response['errors'][0]['message'])

        return response

    @staticmethod
    def _followsToList(user, response):
        follows = []
        for follow in response['data']:
            followInstance = TwitterUser.createFromDict(follow)
            followInstance.saveSingleFollower(user)
            follows.append(followInstance)
        return follows

    def getFollowers(self, user):
        """
        Basic Account v2 API: Follow look-up: 15 requests per 15 minutes
        This function requests followers from an account
        :param user: user instance from that followers should be obtained
        :return: list of followers from user that was specified by input
        """
        max_requests = 15
        numFollowers = user.getFollowersCount()
        # todo: [postponed] problem, how to weight how many iterations, making exponential differences linear, 20000 instead 15000 contacts or mapping to a function with upper and lower limit
        iterations = math.ceil(numFollowers / 1000)
        if iterations > max_requests:
            iterations = max_requests

        response = self._getFollowsResponse(user=user, Friends=False)
        followers = self._followsToList(user, response)

        # todo: [o] request security/robustness regarding limits -> time sleep, try and catch
        # todo: [o] importance sampling
        for i in range(0, iterations):

            if 'next_token' in response['meta'].keys():
                token = response['meta']['next_token']

                response = self._getFollowsResponse(user=user, Friends=False, firstPage=False, token=token)

                if 'errors' in response.keys():
                    raise APIError(response['errors'][0]['message'])

                followers.extend(self._followsToList(user, response))

            else:
                return followers

    def getFriends(self, user):
        """
        Basic Account v2 API: Follow look-up: 15 requests per 15 minutes
        This function requests friends from an account

        desired usage:
        userInstanceFriends = api.getFriends(userInstance)

        :param user: user instance from that friends should be obtained
        :return: list of friends from user that was specified by input
        """
        max_requests = 15
        numFriends = user.getFriendsCount()
        # todo: [postponed] problem, how to weight how many iterations, making exponential differences linear, 20000 instead 15000 contacts or mapping to a function with upper and lower limit
        iterations = math.ceil(numFriends / 1000)
        if iterations > max_requests:
            iterations = max_requests

        response = self._getFollowsResponse(user=user)
        friends = self._followsToList(user, response)

        # todo: [o] request security/robustness regarding limits -> time sleep, try and catch
        # todo: [o] importance sampling
        for i in range(0, iterations):
            if 'next_token' in response['meta'].keys():
                token = response['meta']['next_token']
                response = self._getFollowsResponse(user=user, Friends=True, firstPage=False, token=token)

                if 'errors' in response.keys():
                    raise APIError(response['errors'][0]['message'])

                friends.extend(self._followsToList(user, response))
            else:
                return friends

    def getTweetsByUsername(self, username):
        """
        Basic/Academic Account v2 API: Tweet lookup 300(aps)/900(user)
        after providing the username, the function returns the last xx tweets
        :param username: username of the twitter account you want to have the tweets from
        :return: last x tweets
        """
        str_input = "tweets/search/recent"
        params = {'query': f'(from:{username})'}
        response = self._makeRequest(str_input, params)
        return response['data']

    def getUser(self, id=None, userName=None, userIds=None, userNames=None, withExpansion=False):
        """
        Basic/Academic Account v2 API: user-lookup: 300(aps)/900(user) lookups requests per 15 minutes
        :param userNames: list of user names from that user data should be requested
        :param withExpansion: request additional data objects that relate to the originally returned users
        :param id/userName: user id or username of account to look-up
        :param userIds list of user ids from that user data should be requested
        :return: user instance defined in class TwitterUser2
        """
        if not any([id, userName, userIds, userNames]):
            raise APIError("Please provide id or Username or list of UserIds")

        params = {"user.fields": self._userFields}

        if id:
            str_input = f"users/{id}"

        if userName:
            str_input = f"users/by/username/{userName}"

        if userIds:
            str_input = "users"
            params['ids'] = ','.join([str(u) for u in userIds])

        if userNames:
            str_input = "users/by"
            params['usernames'] = ','.join([u for u in userNames])

        if withExpansion:
            params["expansions"] = "pinned_tweet_id"
        response = self._makeRequest(str_input, params)
        if 'errors' in response.keys():
            raise APIError(response['errors'][0]['message'])

        user = TwitterUser.createFromDict(response['data'])  # key needed to make method in TwitterUser working for other cases as well
        return user

    def getLikedTweetsByUserId(self, userid):
        """
        Basic/Academic Account v2 API: Tweet lookup 75(aps)/75(user)
        :param userid: of account you want to see the liked tweets
        :return: json format of response
        """
        str_input = f"users/{userid}/liked_tweets"
        response = self._makeRequest(str_input)
        return response
