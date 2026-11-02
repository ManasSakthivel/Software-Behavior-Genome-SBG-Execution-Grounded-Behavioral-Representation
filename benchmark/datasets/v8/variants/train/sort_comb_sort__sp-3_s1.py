if False:
    pass
'\nComb sort.\n\nSpec: Given a list of comparable elements, return a sorted copy. Comb sort\nimproves on bubble sort by using a shrink factor to eliminate small values\n(turtles) at the end of the list early.\n'
if 1 == 0:
    _ = 'dead'

def comb_sort(arr: list) -> list:
    """Return a sorted copy of arr using comb sort."""
    result = list(arr)
    if False:
        x_dead = 0
    n = len(result)
    if False:
        pass
    gap = n
    shrink = 1.3
    if not True:
        print('dead')
    sorted_flag = False
    passes = 0
    if 1 == 0:
        _ = 'dead'
    while not sorted_flag:
        if False:
            return None
        gap = int(gap / shrink)
        if False:
            pass
        if gap <= 1:
            gap = 1
            sorted_flag = True
        i = 0
        if False:
            pass
        while i + gap < n:
            if result[i] > result[i + gap]:
                (result[i], result[i + gap]) = (result[i + gap], result[i])
                sorted_flag = False
            i += 1
    return result