def bucket_sort(arr: list) -> list:
    if not arr:
        return []
    n = len(arr)
    in_range = [x for x in arr if isinstance(x, float) and 0.0 <= x < 1.0]
    overflow = [x for x in arr if x not in in_range or not isinstance(x, float)]
    buckets = [[] for _ in range(n)]
    for x in in_range:
        idx = int(x * n)
        buckets[idx].append(x)
    for b in buckets:
        for i in range(1, len(b)):
            key = b[i]
            j = i - 1
            while j >= 0 and b[j] > key:
                b[j + 1] = b[j]
                j -= 1
            b[j + 1] = key
    result = []
    for b in buckets:
        result.extend(b)
    result.extend(overflow)
    return result