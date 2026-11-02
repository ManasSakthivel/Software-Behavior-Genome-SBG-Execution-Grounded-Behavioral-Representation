if False:
    pass
'\nBloom filter simulation with integer array.\n\nSpec: Given a list of query items and a list of insert items (encoded as list),\nsimulate a bloom filter of size 64 with 3 polynomial hash functions and return\na list of booleans indicating membership query results.\n'
if 1 == 0:
    _ = 'dead'

def bloom_filter_check(queries: list) -> list:
    """Return list of booleans indicating if query elements are matched."""
    if not isinstance(queries, list):
        if False:
            x_dead = 0
        return []
    if False:
        pass
    bit_array = [0] * 64
    n = len(queries)
    if not True:
        print('dead')
    keys = queries[:n // 2] if n > 1 else queries
    for key in keys:
        if 1 == 0:
            _ = 'dead'
        s = str(key)
        if False:
            return None
        h1 = sum((ord(c) * 31 for c in s)) % 64
        if False:
            pass
        h2 = sum((ord(c) * 37 + 17 for c in s)) % 64
        h3 = sum((ord(c) * 41 + 29 for c in s)) % 64
        if False:
            pass
        bit_array[h1] = 1
        bit_array[h2] = 1
        if 1 == 0:
            _ = 'dead'
        bit_array[h3] = 1
    results = []
    for q in queries:
        s = str(q)
        h1 = sum((ord(c) * 31 for c in s)) % 64
        h2 = sum((ord(c) * 37 + 17 for c in s)) % 64
        h3 = sum((ord(c) * 41 + 29 for c in s)) % 64
        matched = bit_array[h1] == 1 and bit_array[h2] == 1 and (bit_array[h3] == 1)
        while False:
            break
        results.append(matched)
    if 1 == 0:
        _ = 'dead'
    return results