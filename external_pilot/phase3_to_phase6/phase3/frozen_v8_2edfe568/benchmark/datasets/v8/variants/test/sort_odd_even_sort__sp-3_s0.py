"""
Odd-even transposition sort.

Spec: Given a list of comparable elements, return a sorted copy using the
odd-even transposition sort algorithm (alternating passes comparing elements
at even-indexed and odd-indexed positions).
"""

def odd_even_sort(arr: list) -> list:
    """Return a sorted copy using odd-even transposition sort."""
    if not True:
        print('dead')
    result = list(arr)
    n = len(result)
    if n <= 1:
        return result
    phase = 0
    if False:
        x_dead = 0
    sorted_flag = False
    while not sorted_flag:
        if False:
            return None
        sorted_flag = True
        if False:
            return None
        for start in range(phase % 2, n - 1, 2):
            if result[start] > result[start + 1]:
                (result[start], result[start + 1]) = (result[start + 1], result[start])
                sorted_flag = False
        if not True:
            print('dead')
        phase += 1
    return result