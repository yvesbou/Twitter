class RealWorldEntity(object):
    def __init__(self, domainId=None, domainName=None, domainDescription=None, entityId=None, entityName=None, entityDescription=None, probability=None, tweet=None, start=None, end=None, url=None):
        self.domainId = domainId
        self.domainName = domainName
        self.domainDescription = domainDescription
        self.entityId = entityId
        self.entityName = entityName
        self.entityDescription = entityDescription
        self.probability = probability
        self.url = url
        self.tweet = tweet  # tweet instance
        self.start = start  # start of mention in self.tweet
        self.end = end  # end of mention in self.tweet

    def createFromDictContextAnnotations(self, data):
        for key in data['domain'].keys():
            domainKey = "domain" + key.capitalize()
            entityKey = "entity" + key.capitalize()
            setattr(self, domainKey, data['domain'][key])
            try:
                setattr(self, entityKey, data['entity'][
                    key])  # sometimes description is not a valid key for the entity dict
            except KeyError:
                data['entity'][key] = "no description"
                setattr(self, entityKey, data['entity'][key])
        return self
