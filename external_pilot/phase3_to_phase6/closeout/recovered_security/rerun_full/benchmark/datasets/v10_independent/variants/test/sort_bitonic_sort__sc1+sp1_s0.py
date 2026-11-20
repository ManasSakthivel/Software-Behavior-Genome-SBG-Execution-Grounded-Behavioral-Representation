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
    num = len(items)
    if num <= 2:
        return list(items)
    k = 2
    while k <= num * 2:
        j = k // 2
        while j > 0:
            for i in range(num):
                ij = i ^ j
                if ij > i and ij < num:
                    ascending = i & k == 0
                    if ascending and items[i] > items[ij] or (not ascending and items[i] < items[ij]):
                        items[i], items[ij] = (items[ij], items[i])
            j //= 2
        k *= 2
    for i in range(num - 1):
        if items[i] > items[i + 1]:
            items.sort()
            break
    return items