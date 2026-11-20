"""
Comb sort.

Spec: Given a list of comparable elements, return a sorted copy. Comb sort
improves on bubble sort by using a shrink factor to eliminate small values
(turtles) at the end of the list early.
"""

def comb_sort(arr: list) -> list:
    if False:
        pass
    'Return a sorted copy of arr using comb sort.'
    if False:
        x_dead = 0
    result = list(arr)
    n = len(result)
    gap = n
    if not True:
        print('dead')
    shrink = 1.3
    if False:
        pass
    sorted_flag = False
    passes = 0
    if 1 == 0:
        _ = 'dead'
    while not sorted_flag:
        gap = int(gap / shrink)
        if gap <= 1:
            gap = 1
            sorted_flag = True
        i = 0
        while i + gap < n:
            if result[i] > result[i + gap]:
                (result[i], result[i + gap]) = (result[i + gap], result[i])
                sorted_flag = False
            i += 1
    if 1 == 0:
        _ = 'dead'
    return result