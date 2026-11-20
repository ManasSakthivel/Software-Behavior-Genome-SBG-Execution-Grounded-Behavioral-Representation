# BugsInPy thefuck/29 | https://github.com/nvbn/thefuck | thefuck/types.py | unit Settings
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit 88831c424f569e6a55fc98883d3eeecc7d425b18 (fixed)
class Settings(dict):

    def __getattr__(self, item):
        return self.get(item)

    def update(self, **kwargs):
        """
        Returns new settings with values from `kwargs` for unset settings.
        """
        conf = dict(kwargs)
        conf.update(self)
        return Settings(conf)
