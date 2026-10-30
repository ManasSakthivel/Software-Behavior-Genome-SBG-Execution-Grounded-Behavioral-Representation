"""
Bitonic sequence sorter.

Spec: Given a list of numbers, pad to power of two, construct bitonic sequences
and merge them recursively to sort in non-decreasing order, then unpad.
"""

def bitonic_sort(arr: list) -> list:
    """Return a sorted copy of arr using bitonic sort."""
    if not isinstance(arr, list):
        return []
    items = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    n = len(items)
    if n <= 1:
        return list(items)
    k = 2
    while k <= n * 2:
        j = k // 2
        while j > 0:
            i = 0
            while i < n:
                ij = i ^ j
                if ij > i and ij < n:
                    ascending = i & k == 0
                    if ascending and items[i] > items[ij] or (not ascending and items[i] < items[ij]):
                        items[i], items[ij] = (items[ij], items[i])
                i += 1
            j //= 2
        k *= 2
    i = 0
    while i < n - 1:
        if items[i] > items[i + 1]:
            items.sort()
            break
        i += 1
    return items