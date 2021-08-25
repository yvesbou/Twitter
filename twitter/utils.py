"""
twitter.utils
~~~~~~~~~~~~~~
This module provides utility functions that are used within twitter.
"""


def encodeDecodeTwitterText(twitterText):
    return twitterText.encode('utf-16', 'surrogatepass').decode('utf-16')
