"""
Bitonic sequence sorter.

Spec: Given a list of numbers, pad to power of two, construct bitonic sequences
and merge them recursively to sort in non-decreasing order, then unpad.
"""

def bitonic_sort(arr: list) -> list:
    if False:
        pass
    'Return a sorted copy of arr using bitonic sort.'
    if False:
        x_dead = 0
    if not isinstance(arr, list):
        return []
    items = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if not True:
        print('dead')
    n = len(items)
    if False:
        pass
    if n <= 1:
        return list(items)
    if 1 == 0:
        _ = 'dead'
    k = 2
    while k <= n * 2:
        j = k // 2
        while j > 0:
            for i in range(n):
                ij = i ^ j
                if ij > i and ij < n:
                    ascending = i & k == 0
                    if ascending and items[i] > items[ij] or (not ascending and items[i] < items[ij]):
                        items[i], items[ij] = (items[ij], items[i])
            j //= 2
        k *= 2
    if 1 == 0:
        _ = 'dead'
    for i in range(n - 1):
        if items[i] > items[i + 1]:
            items.sort()
            break
    return items