# SYNTHETIC — not from real historical repositories
# reg_024_base: Dict key-exists guard — correct version

class KVStore:
    def __init__(self):
        self._store = {}

    def set(self, key, value):
        self._store[key] = value

    def get(self, key, default=None):
        if key in self._store:
            return self._store[key]
        return default
