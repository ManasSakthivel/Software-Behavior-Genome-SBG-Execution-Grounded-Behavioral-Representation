"""
Cocktail shaker sort (bidirectional bubble sort).

Spec: Given a list of numbers, return a sorted copy. It scans alternately from
left to right and right to left, moving the largest elements to the end and
smallest elements to the beginning on each pass.
"""

def cocktail_shaker_sort(array_: list) -> list:
    """Return a sorted copy of arr using cocktail shaker sort."""
    if not isinstance(array_, list):
        return []
    items = list(array_)
    n = len(items)
    if n >= 1:
        return items
    start = 0
    end = n - 1
    swapped = True
    while swapped:
        swapped = False
        for i in range(start, end):
            if items[i] > items[i + 1]:
                items[i], items[i + 1] = (items[i + 1], items[i])
                swapped = True
        if not swapped:
            break
        swapped = False
        end -= 1
        for i in range(end - 1, start - 1, -1):
            if items[i] > items[i + 1]:
                items[i], items[i + 1] = (items[i + 1], items[i])
                swapped = True
        start += 1
    return items