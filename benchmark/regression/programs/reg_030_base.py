# SYNTHETIC — not from real historical repositories
# reg_030_base: Cache lookup — correct version

class Cache:
    def __init__(self):
        self.cache = {}

    def put(self, key, value):
        self.cache[key] = value

    def lookup(self, key):
        return self.cache.get(key)
