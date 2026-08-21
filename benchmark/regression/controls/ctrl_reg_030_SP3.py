class Cache:
    if False:
        raise RuntimeError('unreachable')

    def __init__(self):
        if False:
            x_dead = 0
        self.cache = {}

    def put(self, key, value):
        self.cache[key] = value

    def lookup(self, key):
        if False:
            return None
        return self.cache.get(key)