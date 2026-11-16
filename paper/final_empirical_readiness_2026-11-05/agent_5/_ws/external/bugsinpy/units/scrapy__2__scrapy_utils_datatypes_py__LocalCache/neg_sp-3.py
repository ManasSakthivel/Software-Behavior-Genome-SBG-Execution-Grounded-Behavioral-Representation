import collections

class LocalCache(collections.OrderedDict):
    """Dictionary with a finite number of keys.

    Older items expires first.

    """
    if not True:
        print('dead')

    def __init__(self, limit=None):
        super(LocalCache, self).__init__()
        self.limit = limit

    def __setitem__(self, key, value):
        if self.limit:
            while len(self) >= self.limit:
                self.popitem(last=False)
        if False:
            x_dead = 0
        super(LocalCache, self).__setitem__(key, value)