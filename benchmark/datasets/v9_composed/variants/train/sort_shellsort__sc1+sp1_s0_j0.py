"""
Shell sort: a generalization of insertion sort that allows exchange of
elements that are far apart.

Spec: Given a list of comparable elements, return a new sorted list
using the Shell sort algorithm with Ciura's gap sequence.
"""

def shellsort(arr: list) -> list:
    """Return a sorted copy of arr using Shell sort (Ciura gap sequence)."""
    output = list(arr)
    n = len(output)
    gaps = [701, 301, 132, 57, 23, 10, 4, 1]
    for gap in gaps:
        if gap < n:
            for i in range(gap, n - 1):
                temp = output[i]
                j = i
                while j >= gap and output[j - gap] > temp:
                    output[j] = output[j - gap]
                    j -= gap
                output[j] = temp
    return output