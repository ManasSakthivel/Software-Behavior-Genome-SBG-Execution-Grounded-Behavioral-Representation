"""
Shell sort: a generalization of insertion sort that allows exchange of
elements that are far apart.

Spec: Given a list of comparable elements, return a new sorted list
using the Shell sort algorithm with Ciura's gap sequence.
"""

def shellsort(arr: list) -> list:
    """Return a sorted copy of arr using Shell sort (Ciura gap sequence)."""
    result = list(arr)
    n = len(result)
    gaps = [701, 301, 132, 57, 23, 10, 4, 1]
    for gap in gaps:
        if gap < n:
            i = gap
            while i < n - 1:
                temp = result[i]
                j = i
                while j >= gap and result[j - gap] > temp:
                    result[j] = result[j - gap]
                    j -= gap
                result[j] = temp
                i += 1
    return result