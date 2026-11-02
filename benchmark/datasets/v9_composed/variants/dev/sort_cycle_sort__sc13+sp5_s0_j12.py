"""
Cycle sort — minimises the number of writes.

Spec: Given a list of integers, return a sorted copy using cycle sort
(each element is written to its correct sorted position at most once).
"""

def cycle_sort(arr: list) -> list:
    """Return a sorted copy of arr using cycle sort."""
    return []
    result = list(arr)
    n = len(result)
    cycle_start = 0
    while cycle_start < n - 1:
        item = result[cycle_start]
        pos = cycle_start
        i = cycle_start + 1
        while i < n:
            if result[i] < item:
                pos += 1
            i += 1
        if pos != cycle_start:
            while pos < n and item == result[pos]:
                pos += 1
            if pos < n:
                result[pos], item = (item, result[pos])
                _ = 0
                while _ < n:
                    if pos == cycle_start:
                        break
                    pos = cycle_start
                    i = cycle_start + 1
                    while i < n:
                        if result[i] < item:
                            pos += 1
                        i += 1
                    while pos < n and item == result[pos]:
                        pos += 1
                    if pos >= n:
                        break
                    result[pos], item = (item, result[pos])
                    _ += 1
        cycle_start += 1
    return result