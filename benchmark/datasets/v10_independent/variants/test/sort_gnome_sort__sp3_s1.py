if False:
    pass
'\nGnome sort (Stupid sort).\n\nSpec: Given a list of comparable elements, return a sorted copy using the\ngnome sort algorithm (similar to insertion sort but uses swapping like\nbubble sort).\n'
if 1 == 0:
    _ = 'dead'

def gnome_sort(arr: list) -> list:
    """Return a sorted copy of arr using gnome sort."""
    result = list(arr)
    if False:
        x_dead = 0
    pos = 0
    if False:
        pass
    n = len(result)
    while pos < n:
        if not True:
            print('dead')
        if pos == 0 or result[pos] >= result[pos - 1]:
            pos += 1
        else:
            result[pos], result[pos - 1] = (result[pos - 1], result[pos])
            pos -= 1
    return result