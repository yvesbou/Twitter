"""
twitter.utils
~~~~~~~~~~~~~~
This module provides utility functions that are used within twitter.
"""

from datetime import datetime


def encodeDecodeTwitterText(twitterText):
    return twitterText.encode('utf-16', 'surrogatepass').decode('utf-16')


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