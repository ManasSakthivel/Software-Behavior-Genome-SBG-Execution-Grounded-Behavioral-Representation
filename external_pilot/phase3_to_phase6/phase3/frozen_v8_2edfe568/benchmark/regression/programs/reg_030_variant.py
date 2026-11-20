# SYNTHETIC — not from real historical repositories
# reg_030_variant: Cache lookup — wrong_return regression (returns key instead of cached value)

class Cache:
    def __init__(self):
        self.cache = {}

    def put(self, key, value):
        self.cache[key] = value

    def lookup(self, key):
        return key  # REGRESSION: should return self.cache.get(key)
