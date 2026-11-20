"""
Cycle sort — minimises the number of writes.

Spec: Given a list of integers, return a sorted copy using cycle sort
(each element is written to its correct sorted position at most once).
"""

def _extracted_2_0(arr):
    """Return a sorted copy of arr using cycle sort."""
    result = list(arr)
    return result

def cycle_sort(arr: list) -> list:
    result = _extracted_2_0(arr)
    n = len(result)
    for cycle_start in range(n - 1):
        item = result[cycle_start]
        pos = cycle_start
        for i in range(cycle_start + 1, n):
            if result[i] < item:
                pos += 1
        if pos == cycle_start:
            continue
        while item == result[pos]:
            pos += 1
        (result[pos], item) = (item, result[pos])
        while pos != cycle_start:
            pos = cycle_start
            for i in range(cycle_start + 1, n):
                if result[i] < item:
                    pos += 1
            while item == result[pos]:
                pos += 1
            (result[pos], item) = (item, result[pos])
    return result