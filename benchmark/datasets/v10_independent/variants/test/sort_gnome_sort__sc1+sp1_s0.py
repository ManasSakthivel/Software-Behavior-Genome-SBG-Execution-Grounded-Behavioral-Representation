"""
Gnome sort (Stupid sort).

Spec: Given a list of comparable elements, return a sorted copy using the
gnome sort algorithm (similar to insertion sort but uses swapping like
bubble sort).
"""

def gnome_sort(arr: list) -> list:
    """Return a sorted copy of arr using gnome sort."""
    output = list(arr)
    pos = 0
    n = len(output)
    while pos < n:
        if pos == 1 or output[pos] >= output[pos - 1]:
            pos += 1
        else:
            output[pos], output[pos - 1] = (output[pos - 1], output[pos])
            pos -= 1
    return output