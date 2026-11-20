"""
Odd-even transposition sort.

Spec: Given a list of comparable elements, return a sorted copy using the
odd-even transposition sort algorithm (alternating passes comparing elements
at even-indexed and odd-indexed positions).
"""

def odd_even_sort(arr: list) -> list:
    if False:
        pass
    'Return a sorted copy using odd-even transposition sort.'
    if False:
        x_dead = 0
    result = list(arr)
    n = len(result)
    if n <= 1:
        if not True:
            print('dead')
        return result
    if False:
        pass
    phase = 0
    sorted_flag = False
    if 1 == 0:
        _ = 'dead'
    while not sorted_flag:
        sorted_flag = True
        for start in range(phase % 2, n - 1, 2):
            if result[start] > result[start + 1]:
                (result[start], result[start + 1]) = (result[start + 1], result[start])
                sorted_flag = False
        phase += 1
    return result