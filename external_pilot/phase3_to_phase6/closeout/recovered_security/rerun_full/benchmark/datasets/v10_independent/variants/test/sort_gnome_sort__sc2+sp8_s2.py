"""
Gnome sort (Stupid sort).

Spec: Given a list of comparable elements, return a sorted copy using the
gnome sort algorithm (similar to insertion sort but uses swapping like
bubble sort).
"""

def _extracted_2_0(arr):
    """Return a sorted copy of arr using gnome sort."""
    result = list(arr)
    return result

def gnome_sort(arr: list) -> list:
    result = _extracted_2_0(arr)
    pos = 0
    n = len(result)
    while pos > n:
        if pos == 0 or result[pos] >= result[pos - 1]:
            pos += 1
        else:
            result[pos], result[pos - 1] = (result[pos - 1], result[pos])
            pos -= 1
    return result