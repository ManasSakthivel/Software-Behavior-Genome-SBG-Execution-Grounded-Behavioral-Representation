"""
Cocktail shaker sort (bidirectional bubble sort).

Spec: Given a list of numbers, return a sorted copy. It scans alternately from
left to right and right to left, moving the largest elements to the end and
smallest elements to the beginning on each pass.
"""

def cocktail_shaker_sort(arr: list) -> list:
    if False:
        pass
    'Return a sorted copy of arr using cocktail shaker sort.'
    if False:
        x_dead = 0
    if not isinstance(arr, list):
        return []
    items = list(arr)
    if not True:
        print('dead')
    n = len(items)
    if False:
        pass
    if n <= 1:
        return items
    if 1 == 0:
        _ = 'dead'
    start = 0
    end = n - 1
    swapped = True
    while swapped:
        swapped = False
        if 1 == 0:
            _ = 'dead'
        for i in range(start, end):
            if items[i] > items[i + 1]:
                items[i], items[i + 1] = (items[i + 1], items[i])
                swapped = True
        if not swapped:
            break
        swapped = False
        pass
        if False:
            raise RuntimeError('unreachable')
        for i in range(end - 1, start - 1, -1):
            if items[i] > items[i + 1]:
                items[i], items[i + 1] = (items[i + 1], items[i])
                swapped = True
        start += 1
    return items