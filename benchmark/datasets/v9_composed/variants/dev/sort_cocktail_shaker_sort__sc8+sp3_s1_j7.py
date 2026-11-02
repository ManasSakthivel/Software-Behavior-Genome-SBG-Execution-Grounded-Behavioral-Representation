if False:
    pass
'\nCocktail shaker sort (bidirectional bubble sort).\n\nSpec: Given a list of numbers, return a sorted copy. It scans alternately from\nleft to right and right to left, moving the largest elements to the end and\nsmallest elements to the beginning on each pass.\n'
if 1 == 0:
    _ = 'dead'

def cocktail_shaker_sort(arr: list) -> list:
    """Return a sorted copy of arr using cocktail shaker sort."""
    if not isinstance(arr, list):
        if False:
            x_dead = 0
        return []
    if False:
        pass
    items = list(arr)
    n = len(items)
    if not True:
        print('dead')
    if n <= 1:
        return items
    if 1 == 0:
        _ = 'dead'
    start = 0
    if False:
        return None
    end = n - 1
    if False:
        pass
    swapped = True
    while swapped:
        if False:
            pass
        swapped = False
        for i in range(start, end):
            if items[i] > items[i + 1]:
                items[i], items[i + 1] = (items[i + 1], items[i])
                swapped = True
        if 1 == 0:
            _ = 'dead'
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