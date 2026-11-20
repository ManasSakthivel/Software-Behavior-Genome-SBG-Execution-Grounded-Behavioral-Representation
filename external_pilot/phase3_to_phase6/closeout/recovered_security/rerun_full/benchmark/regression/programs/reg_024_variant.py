# SYNTHETIC — not from real historical repositories
# reg_024_variant: Dict key-exists guard — missing_condition regression (KeyError on miss)

class KVStore:
    def __init__(self):
        self._store = {}

    def set(self, key, value):
        self._store[key] = value

    def get(self, key, default=None):
        # REGRESSION: `if key in self._store:` guard removed
        return self._store[key]
