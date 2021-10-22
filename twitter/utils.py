"""
twitter.utils
~~~~~~~~~~~~~~
This module provides utility functions that are used within twitter.
"""

from datetime import datetime


def encodeDecodeTwitterText(twitterText):
    """
    used in create TweetFromDict, UserFromDict, PollFromDict
    :param twitterText:
    :return:
    """
    return twitterText.encode('utf-16', 'surrogatepass').decode('utf-16').encode('utf-8').decode('utf-8')


def datetime_valid(dt_str):
    try:
        datetime.fromisoformat(dt_str)
    except:
        try:
            datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            return False
        return True
    return True


def IfWaitTooLong(now, then):
    diff = then - now
    if diff > 30:
        return True
    else:
        return False
