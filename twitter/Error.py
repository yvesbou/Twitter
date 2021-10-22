from http.client import HTTPException


class APIError(Exception):
    def message(self):
        """Returns the first argument used to construct this error."""
        return self.args[0]


class EmptyPageError(Exception):
    pass


class LimitExceedError(Exception):
    pass


class UnsavedDataLimitExceedError(Exception):
    pass


class TweetCapExceedingError(Exception):
    pass


class BadRequest(HTTPException):
    """400 HTTP status code"""
    pass


class Unauthorized(HTTPException):
    """401 HTTP status code"""
    pass


class Forbidden(HTTPException):
    """403 HTTP status code"""
    pass


class NotFound(HTTPException):
    """404 HTTP status code"""
    pass


class TooManyRequests(HTTPException):
    """429 HTTP status code"""
    pass


class TwitterServerError(HTTPException):
    """5xx HTTP status code"""
    pass
