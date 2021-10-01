class APIError(Exception):
    def message(self):
        """Returns the first argument used to construct this error."""
        return self.args[0]


class EmptyPageError(Exception):
    pass


