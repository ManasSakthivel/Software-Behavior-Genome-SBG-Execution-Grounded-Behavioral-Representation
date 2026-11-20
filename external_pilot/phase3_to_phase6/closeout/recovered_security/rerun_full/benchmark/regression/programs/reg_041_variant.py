# SYNTHETIC — not from real historical repositories
# reg_041_variant: LRU cache capacity — wrong_constant regression (127 instead of 128)

from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity=127):  # REGRESSION: should be 128
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key):
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
