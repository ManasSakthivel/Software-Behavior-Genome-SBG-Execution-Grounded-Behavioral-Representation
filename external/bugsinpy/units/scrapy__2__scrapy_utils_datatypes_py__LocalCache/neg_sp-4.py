import collections

class LocalCache(collections.OrderedDict):

    def __init__(self, limit=None):
        super(LocalCache, self).__init__()
        self.limit = limit

    def __setitem__(self, key, value):
        if self.limit:
            while len(self) >= self.limit:
                self.popitem(last=False)
        super(LocalCache, self).__setitem__(key, value)