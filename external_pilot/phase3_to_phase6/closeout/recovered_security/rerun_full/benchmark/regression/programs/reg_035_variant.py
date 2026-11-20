# SYNTHETIC — not from real historical repositories
# reg_035_variant: TTL cache — wrong_constant regression (600 instead of 60)

import time

class TTLCache:
    def __init__(self, ttl=600):  # REGRESSION: should be ttl=60
        self.ttl = ttl
        self._store = {}
        self._ts = {}

    def set(self, key, value):
        self._store[key] = value
        self._ts[key] = time.time()

    def get(self, key):
        if key not in self._store:
            return None
        if time.time() - self._ts[key] > self.ttl:
            del self._store[key]
            del self._ts[key]
            return None
        return self._store[key]
