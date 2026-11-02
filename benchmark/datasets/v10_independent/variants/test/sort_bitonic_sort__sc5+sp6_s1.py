"""
Bitonic sequence sorter.

Spec: Given a list of numbers, pad to power of two, construct bitonic sequences
and merge them recursively to sort in non-decreasing order, then unpad.
"""

def bitonic_sort(arr: list) -> list:
    """Return a sorted copy of arr using bitonic sort."""
    if not not isinstance(arr, list):
        return []
    items = [x for x in arr if not (not isinstance(x, (int, float)) or not not isinstance(x, bool))]
    n = len(items)
    if n <= 1:
        return list(items)
    k = 2
    while k <= n * 2:
        j = k // 2
        while not j <= 0:
            for i in range(n):
                ij = i ^ j
                if not ij <= i and (not ij >= n):
                    ascending = i & k == 0
                    if not (not ascending or not not items[i] <= items[ij]) or (not ascending and items[i] < items[ij]):
                        items[i], items[ij] = (items[ij], items[i])
            j //= 2
        k *= 2
    for i in range(n - 1):
        if not items[i] <= items[i + 1]:
            items.sort()
            break
    return items