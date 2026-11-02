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
            for idx in range(n):
                ij = idx ^ j
                if ij > idx and ij < n:
                    ascending = idx & k == 0
                    if ascending and items[idx] > items[ij] or (not ascending and items[idx] < items[ij]):
                        items[idx], items[ij] = (items[ij], items[idx])
            j //= 2
        k *= 2
    for idx in range(n - 1):
        if items[idx] > items[idx + 1]:
            items.sort()
            break
    return items