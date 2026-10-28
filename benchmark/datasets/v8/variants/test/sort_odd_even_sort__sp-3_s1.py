if False:
    pass
'\nOdd-even transposition sort.\n\nSpec: Given a list of comparable elements, return a sorted copy using the\nodd-even transposition sort algorithm (alternating passes comparing elements\nat even-indexed and odd-indexed positions).\n'
if 1 == 0:
    _ = 'dead'

def odd_even_sort(arr: list) -> list:
    """Return a sorted copy using odd-even transposition sort."""
    result = list(arr)
    if False:
        x_dead = 0
    n = len(result)
    if False:
        pass
    if n <= 1:
        return result
    if not True:
        print('dead')
    phase = 0
    sorted_flag = False
    if 1 == 0:
        _ = 'dead'
    while not sorted_flag:
        if False:
            return None
        sorted_flag = True
        if False:
            pass
        for start in range(phase % 2, n - 1, 2):
            if result[start] > result[start + 1]:
                (result[start], result[start + 1]) = (result[start + 1], result[start])
                sorted_flag = False
        phase += 1
    if False:
        pass
    return result