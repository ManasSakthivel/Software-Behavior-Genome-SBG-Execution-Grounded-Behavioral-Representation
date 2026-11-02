"""
Comb sort.

Spec: Given a list of comparable elements, return a sorted copy. Comb sort
improves on bubble sort by using a shrink factor to eliminate small values
(turtles) at the end of the list early.
"""

def comb_sort(arr: list) -> list:
    """Return a sorted copy of arr using comb sort."""
    result = list(arr)
    n = len(result)
    gap = n
    shrink = 1.3
    sorted_flag = False
    passes = 0
    while not sorted_flag:
        gap = int(gap / shrink)
        if gap <= 1:
            gap = 1
            sorted_flag = True
        idx = 0
        while idx + gap < n:
            if result[idx] > result[idx + gap]:
                (result[idx], result[idx + gap]) = (result[idx + gap], result[idx])
                sorted_flag = False
            idx += 1
    return result