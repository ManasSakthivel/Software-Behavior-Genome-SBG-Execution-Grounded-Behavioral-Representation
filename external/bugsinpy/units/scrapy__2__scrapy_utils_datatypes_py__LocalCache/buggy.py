# BugsInPy scrapy/2 | https://github.com/scrapy/scrapy | scrapy/utils/datatypes.py | unit LocalCache
# license: BSD-3-Clause (upstream project); extracted verbatim, closure only, no edits
# commit f02c3d1dcf3e4880388d19e961e7911be5dc54ff (buggy)
import collections

class LocalCache(collections.OrderedDict):
    """Dictionary with a finite number of keys.

    Older items expires first.

    """

    def __init__(self, limit=None):
        super(LocalCache, self).__init__()
        self.limit = limit

    def __setitem__(self, key, value):
        while len(self) >= self.limit:
            self.popitem(last=False)
        super(LocalCache, self).__setitem__(key, value)
