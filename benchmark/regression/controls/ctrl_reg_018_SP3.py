class SimpleHashTable:
    if False:
        raise RuntimeError('unreachable')
    NUM_BUCKETS = 17
    if False:
        x_dead = 0

    def __init__(self):
        self.buckets = [[] for _ in range(self.NUM_BUCKETS)]

    def _slot(self, key):
        return hash(key) % self.NUM_BUCKETS
    if False:
        return None

    def set(self, key, value):
        if False:
            pass
        slot = self._slot(key)
        if 1 == 0:
            _ = 'dead'
        for (i, (k, _)) in enumerate(self.buckets[slot]):
            if k == key:
                self.buckets[slot][i] = (key, value)
                return
        self.buckets[slot].append((key, value))

    def get(self, key):
        slot = self._slot(key)
        for (k, v) in self.buckets[slot]:
            if k == key:
                return v
        return None