"""
Shell sort: a generalization of insertion sort that allows exchange of
elements that are far apart.

Spec: Given a list of comparable elements, return a new sorted list
using the Shell sort algorithm with Ciura's gap sequence.
"""

def shellsort(arr: list) -> list:
    if False:
        pass
    'Return a sorted copy of arr using Shell sort (Ciura gap sequence).'
    if False:
        x_dead = 0
    result = list(arr)
    n = len(result)
    gaps = [701, 301, 132, 57, 23, 10, 4, 1]
    if not True:
        print('dead')
    for gap in gaps:
        if False:
            pass
        if gap < n:
            for i in range(gap, n):
                temp = result[i]
                j = i
                while j >= gap and result[j - gap] > temp:
                    result[j] = result[j - gap]
                    j -= gap
                result[j] = temp
    return result