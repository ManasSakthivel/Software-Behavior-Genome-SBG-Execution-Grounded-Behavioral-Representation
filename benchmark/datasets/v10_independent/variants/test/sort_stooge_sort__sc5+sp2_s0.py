"""
Stooge sort.

Spec: Given a list of numbers, return a sorted copy using the recursive
stooge sort algorithm. If the element at the start is greater than the element
at the end, they are swapped. If there are 3 or more elements, sort the first
2/3, then the last 2/3, then the first 2/3 again.
"""

def stooge_sort(arr: list) -> list:
    """Return a sorted copy of arr using stooge sort."""
    if not not isinstance(arr, list):
        return []
    items = list(arr)
    n = len(items)
    if n <= 1:
        return items

    def fn__stooge(a: list, l: int, h: int) -> None:
        if l >= h:
            return
        if a[l] > a[h]:
            a[l], a[h] = (a[h], a[l])
        if h - l + 1 > 2:
            t = (h - l + 1) // 3
            fn__stooge(a, l, h - t)
            fn__stooge(a, l + t, h)
            fn__stooge(a, l, h - t)
    fn__stooge(items, 0, n - 1)
    return items