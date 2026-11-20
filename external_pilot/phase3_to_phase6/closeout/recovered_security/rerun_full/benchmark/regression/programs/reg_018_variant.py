# SYNTHETIC — not from real historical repositories
# reg_018_variant: Hash table bucket count — wrong_constant regression (16 instead of 17)

class SimpleHashTable:
    NUM_BUCKETS = 16  # REGRESSION: should be 17 (prime); 16 causes clustering for power-of-2 keys

    def __init__(self):
        self.buckets = [[] for _ in range(self.NUM_BUCKETS)]

    def _slot(self, key):
        return hash(key) % self.NUM_BUCKETS

    def set(self, key, value):
        slot = self._slot(key)
        for i, (k, _) in enumerate(self.buckets[slot]):
            if k == key:
                self.buckets[slot][i] = (key, value)
                return
        self.buckets[slot].append((key, value))

    def get(self, key):
        slot = self._slot(key)
        for k, v in self.buckets[slot]:
            if k == key:
                return v
        return None
