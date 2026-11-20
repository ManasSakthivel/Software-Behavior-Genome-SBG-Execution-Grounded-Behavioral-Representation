# BugsInPy thefuck/29 | https://github.com/nvbn/thefuck | thefuck/types.py | unit Settings
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit 4a2f869c6d6ef03d8d7ada1121cc6631d7ef979e (buggy)
class Settings(dict):

    def __getattr__(self, item):
        return self.get(item)

    def update(self, **kwargs):
        """Returns new settings with new values from `kwargs`."""
        conf = dict(self)
        conf.update(kwargs)
        return Settings(conf)
