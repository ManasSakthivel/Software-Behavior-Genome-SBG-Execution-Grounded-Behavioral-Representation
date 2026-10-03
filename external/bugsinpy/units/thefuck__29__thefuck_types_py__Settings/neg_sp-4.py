class Settings(dict):

    def __getattr__(self, item):
        return self.get(item)

    def update(self, **kwargs):
        conf = dict(kwargs)
        conf.update(self)
        return Settings(conf)