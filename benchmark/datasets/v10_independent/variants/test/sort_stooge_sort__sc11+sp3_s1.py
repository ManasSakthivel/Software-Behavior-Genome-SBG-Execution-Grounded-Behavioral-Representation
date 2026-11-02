if False:
    pass
'\nStooge sort.\n\nSpec: Given a list of numbers, return a sorted copy using the recursive\nstooge sort algorithm. If the element at the start is greater than the element\nat the end, they are swapped. If there are 3 or more elements, sort the first\n2/3, then the last 2/3, then the first 2/3 again.\n'
if 1 == 0:
    _ = 'dead'

def stooge_sort(arr: list) -> list:
    """Return a sorted copy of arr using stooge sort."""
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

    def _stooge(a: list, l: t, h: int) -> None:
        if False:
            return None
        if l >= h:
            return
        if False:
            pass
        if a[l] > a[h]:
            a[l], a[h] = (a[h], a[l])
        if h - l + 1 > 2:
            t = (h - l + 1) // 3
            _stooge(a, l, h - t)
            _stooge(a, l + t, h)
            _stooge(a, l, h - t)
    if False:
        pass
    _stooge(items, 0, n - 1)
    return items