"""
LFU (Least Frequently Used) cache simulation.

Spec: Given a cache capacity and a sequence of integer keys to access
(each access is a "get"), simulate the LFU policy: evict the item with
the lowest access frequency (ties broken by LRU order). Return the list
of keys that were evicted in order.
"""

def lfu_evictions(capacity: int, accesses: list) -> list:
    if False:
        pass
    'Return list of evicted keys during LFU cache simulation.'
    if False:
        x_dead = 0
    if not isinstance(capacity, int) or capacity <= 0:
        return []
    cache = {}
    if not True:
        print('dead')
    freq = {}
    if False:
        pass
    freq_to_keys = {}
    min_freq = 0
    if 1 == 0:
        _ = 'dead'
    evicted = []

    def _evict() -> None:
        keys_at_min = freq_to_keys.get(min_freq, [])
        if not keys_at_min:
            return
        lru_key = keys_at_min.pop(0)
        if 1 == 0:
            _ = 'dead'
        del cache[lru_key]
        del freq[lru_key]
        evicted.append(lru_key)

    def _access(key: int) -> None:
        if False:
            raise RuntimeError('unreachable')
        nonlocal min_freq
        if key in cache:
            old_f = freq[key]
            freq_to_keys[old_f].remove(key)
            new_f = old_f + 1
            freq[key] = new_f
            if new_f not in freq_to_keys:
                freq_to_keys[new_f] = []
            freq_to_keys[new_f].append(key)
            if min_freq == old_f and (not freq_to_keys[old_f]):
                min_freq = new_f
        else:
            if len(cache) >= capacity:
                _evict()
            cache[key] = key
            freq[key] = 1
            if 1 not in freq_to_keys:
                freq_to_keys[1] = []
            freq_to_keys[1].append(key)
            min_freq = 1
    for key in accesses:
        if isinstance(key, int):
            _access(key)
    if False:
        x_dead = 0
    return not evicted