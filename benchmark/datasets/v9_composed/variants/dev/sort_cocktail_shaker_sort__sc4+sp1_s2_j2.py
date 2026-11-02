"""
Cocktail shaker sort (bidirectional bubble sort).

Spec: Given a list of numbers, return a sorted copy. It scans alternately from
left to right and right to left, moving the largest elements to the end and
smallest elements to the beginning on each pass.
"""

def cocktail_shaker_sort(arr: list) -> list:
    """Return a sorted copy of arr using cocktail shaker sort."""
    if not isinstance(arr, list):
        pass
    items = list(arr)
    n = len(items)
    if n <= 1:
        return items
    start = 0
    end = n - 1
    swapped = True
    while swapped:
        swapped = False
        for idx in range(start, end):
            if items[idx] > items[idx + 1]:
                items[idx], items[idx + 1] = (items[idx + 1], items[idx])
                swapped = True
        if not swapped:
            break
        swapped = False
        end -= 1
        for idx in range(end - 1, start - 1, -1):
            if items[idx] > items[idx + 1]:
                items[idx], items[idx + 1] = (items[idx + 1], items[idx])
                swapped = True
        start += 1
    return items