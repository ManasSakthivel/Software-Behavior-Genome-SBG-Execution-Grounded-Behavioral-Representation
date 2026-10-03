# BugsInPy scrapy/2 | https://github.com/scrapy/scrapy | scrapy/utils/datatypes.py | unit LocalCache
# license: BSD-3-Clause (upstream project); extracted verbatim, closure only, no edits
# commit 439a3e59b8e858441f8d97dbc32f398db392330d (fixed)
import collections

class LocalCache(collections.OrderedDict):
    """Dictionary with a finite number of keys.

    Older items expires first.

    """

    def __init__(self, limit=None):
        super(LocalCache, self).__init__()
        self.limit = limit

    def __setitem__(self, key, value):
        if self.limit:
            while len(self) >= self.limit:
                self.popitem(last=False)
        super(LocalCache, self).__setitem__(key, value)
