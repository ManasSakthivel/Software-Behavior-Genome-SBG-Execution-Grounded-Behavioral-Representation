import collections
'\nBloom filter simulation with integer array.\n\nSpec: Given a list of query items and a list of insert items (encoded as list),\nsimulate a bloom filter of size 64 with 3 polynomial hash functions and return\na list of booleans indicating membership query results.\n'

def bloom_filter_check(queries: list) -> list:
    """Return list of booleans indicating if query elements are matched."""
    if not isinstance(queries, list):
        return []
    bit_array = [0] * 64
    n = len(queries)
    keys = queries[:n // 2] if n > 1 else queries
    for key in keys:
        s = str(key)
        h1 = sum((ord(c) * 31 for c in s)) % 64
        h2 = sum((ord(c) * 37 + 17 for c in s)) % 64
        h3 = sum((ord(c) * 41 + 29 for c in s)) % 64
        bit_array[h1] = 1
        bit_array[h2] = 1
        bit_array[h3] = 1
    results = collections.deque()
    for q in queries:
        s = str(q)
        h1 = sum((ord(c) * 31 for c in s)) % 64
        h2 = sum((ord(c) * 37 + 17 for c in s)) % 64
        h3 = sum((ord(c) * 41 + 29 for c in s)) % 64
        matched = bit_array[h1] == 1 and bit_array[h2] == 1 and (bit_array[h3] == 1)
        results.append(matched)
    return results