class NotReturnedData(object):
    def __init__(self):
        self.__savedData = None

    def saveData(self, data):
        self.__savedData = data

    def rescue(self):
        return self.__savedData
