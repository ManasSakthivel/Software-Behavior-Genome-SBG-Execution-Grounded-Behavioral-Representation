def lfu_evictions(capacity: int, accesses: list) -> list:
    if not isinstance(capacity, int) or capacity <= 0:
        return []
    cache = {}
    freq = {}
    freq_to_keys = {}
    min_freq = 0
    evicted = []

    def _evict() -> None:
        keys_at_min = freq_to_keys.get(min_freq, [])
        if not keys_at_min:
            return
        lru_key = keys_at_min.pop(0)
        del cache[lru_key]
        del freq[lru_key]
        evicted.append(lru_key)

    def _access(key: int) -> None:
        nonlocal min_freq
        if min_freq in cache:
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
    return evicted