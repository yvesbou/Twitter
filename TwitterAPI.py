import requests
import math
import time

from TwitterUser import TwitterUser2

from Error import APIError


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

    def getFollowers(self, user):
        # todo: [x] rewrite this function
        """
        Basic Account v2 API: Follow look-up: 15 requests per 15 minutes
        This function requests followers from an account
        :param user: user instance from that followers should be obtained
        :return: the result of the request
        """
        max_requests = 15
        numFollowers = user.getFollowersCount()
        iterations = math.ceil(numFollowers/1000)
        if iterations > max_requests:
            iterations = max_requests
        str_input = "users/" + str(user.id) + "/" + "followers"
        params = {'user.fields': self._userFields, 'max_results': '1000'}
        response = self._makeRequest(str_input, params)
        if 'errors' in response.keys():
            raise APIError(response['errors'][0]['message'])
        followers = []
        for follower in response['data']:
            followers.append(follower)

        for i in range(0, iterations):
            if 'next_token' in response['meta'].keys():
                token = response['meta']['next_token']
                params['pagination_token'] = token
                response = self._makeRequest(str_input, params)
                if 'errors' in response.keys():
                    raise APIError(response['errors'][0]['message'])
                for follower in response['data']:
                    followers.append(follower)
            else:
                return followers

        return followers

    def getFriends(self, user):
        """
        Basic Account v2 API: Follow look-up: 15 requests per 15 minutes
        This function requests friends from an account
        :param user: user instance from that friends should be obtained
        :return: the result of the request
        """
        # todo: [x] make twitter user, in order to obtain follower count
        # todo: [x] w/ follower count compute how long it takes to obtain all followers w/ 15X1000 requests per 15min 60k/hour 1.2M/day
        max_requests = 15
        numFriends = user.getFriendsCount()
        # todo: [postponed] problem, how to weight how many iterations, making exponential differences linear, 20000 instead 15000 contacts or mapping to a function with upper and lower limit
        iterations = math.ceil(numFriends/1000)
        if iterations > max_requests:
            iterations = max_requests
        start = time.time()
        str_input = "users/" + str(user.id) + "/" + "following"
        params = {'user.fields': self._userFields, 'max_results': '1000'}
        friends = []
        response = self._makeRequest(str_input, params)
        # max_requests -= 1
        if 'errors' in response.keys():
            raise APIError(response['errors'][0]['message'])

        for friend in response['data']:
            friends.append(friend)

        # todo: [x] request security/robustness regarding limits
        # todo: [o] importance sampling
        for i in range(0, iterations):
            #if max_requests == 0:
                #now = time.time()
                #if now - start > 15*60:
                    #start = now
                    #continue
                #else:
                    #time.sleep(15*60 - (now-start))
            if 'next_token' in response['meta'].keys():
                token = response['meta']['next_token']
                params['pagination_token'] = token
                response = self._makeRequest(str_input, params)
                # max_requests -= 1
                # print(response)
                if 'errors' in response.keys():
                    raise APIError(response['errors'][0]['message'])
                for friend in response['data']:
                    friends.append(friend)
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
        :return: json format of user profile
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
        return response

    # not used anymore because user instances
    def getUserIdByName(self, username):
        """
        Translating Username to ID
        :param username
        :return: ID
        """
        userid = self.getUser(userName=username)['data']['id']
        return userid

    def getLikedTweetsByUserId(self, userid):
        """
        Basic/Academic Account v2 API: Tweet lookup 75(aps)/75(user)
        :param userid: of account you want to see the liked tweets
        :return: json format of response
        """
        str_input = f"users/{userid}/liked_tweets"
        response = self._makeRequest(str_input)
        return response
