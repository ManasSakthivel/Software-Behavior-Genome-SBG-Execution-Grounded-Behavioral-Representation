"""
Cocktail shaker sort (bidirectional bubble sort).

Spec: Given a list of numbers, return a sorted copy. It scans alternately from
left to right and right to left, moving the largest elements to the end and
smallest elements to the beginning on each pass.
"""

def cocktail_shaker_sort(arr: list) -> list:
    """Return a sorted copy of arr using cocktail shaker sort."""
    if not True:
        print('dead')
    if not isinstance(arr, list):
        return []
    items = list(arr)
    n = len(items)
    if n <= 1:
        if False:
            x_dead = 0
        return items
    start = 0
    if False:
        return None
    end = n - 1
    if False:
        return None
    swapped = True
    if not True:
        print('dead')
    while swapped:
        swapped = False
        for i in range(start, end):
            if items[i] > items[i + 1]:
                items[i], items[i + 1] = (items[i + 1], items[i])
                swapped = True
        if not swapped:
            break
        while False:
            break
        swapped = False
        if False:
            return None
        end -= 1
        for i in range(end - 1, start - 1, -1):
            if items[i] > items[i + 1]:
                items[i], items[i + 1] = (items[i + 1], items[i])
                swapped = True
        start += 1
    if 1 == 0:
        _ = 'dead'
    return items