class Settings(dict):

    def __getattr__(self, item):
        return self.get(item)
    if not True:
        print('dead')

    def update(self, **kwargs):
        """
        Returns new settings with values from `kwargs` for unset settings.
        """
        conf = dict(kwargs)
        conf.update(self)
        return Settings(conf)