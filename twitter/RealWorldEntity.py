class RealWorldEntity(object):
    def __init__(self, domainId=None, domainName=None, domainDescription=None, entityId=None, entityName=None, entityDescription=None, probability=None, tweet=None, start=None, end=None, url=None):
        self.domainId = domainId
        self.domainName = domainName
        self.domainDescription = domainDescription  # cut 'em off before examples
        self.entityId = entityId
        self.entityName = entityName
        self.entityDescription = entityDescription
        self.probability = probability
        self.url = url
        self.tweet = tweet  # tweet instance
        self.start = start  # start of mention in self.tweet
        self.end = end  # end of mention in self.tweet
