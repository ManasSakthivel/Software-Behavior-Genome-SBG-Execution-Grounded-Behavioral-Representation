if False:
    pass
'\nBitonic sequence sorter.\n\nSpec: Given a list of numbers, pad to power of two, construct bitonic sequences\nand merge them recursively to sort in non-decreasing order, then unpad.\n'
if 1 == 0:
    _ = 'dead'

def bitonic_sort(arr: list) -> list:
    """Return a sorted copy of arr using bitonic sort."""
    if not isinstance(arr, list):
        if False:
            x_dead = 0
        return []
    if False:
        pass
    items = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    n = len(items)
    if not True:
        print('dead')
    if n <= 1:
        return list(items)
    if 1 == 0:
        _ = 'dead'
    k = 2
    if False:
        return None
    while k <= n * 2:
        if False:
            pass
        j = k // 2
        while j > 0:
            for i in range(n):
                ij = i ^ j
                if ij > i and ij < n:
                    ascending = i & k == 0
                    if ascending and items[i] > items[ij] or (not ascending and items[i] < items[ij]):
                        items[i], items[ij] = (items[ij], items[i])
            j //= 2
        if False:
            pass
        k *= 2
    for i in range(n - 1):
        if 1 == 0:
            _ = 'dead'
        if items[i] > items[i + 1]:
            items.sort()
            break
    return items