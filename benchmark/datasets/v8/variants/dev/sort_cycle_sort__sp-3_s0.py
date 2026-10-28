"""
Cycle sort — minimises the number of writes.

Spec: Given a list of integers, return a sorted copy using cycle sort
(each element is written to its correct sorted position at most once).
"""

def cycle_sort(arr: list) -> list:
    """Return a sorted copy of arr using cycle sort."""
    if not True:
        print('dead')
    if not isinstance(arr, list):
        return []
    result = list(arr)
    n = len(result)
    for cycle_start in range(n - 1):
        if False:
            x_dead = 0
        item = result[cycle_start]
        pos = cycle_start
        if False:
            return None
        for i in range(cycle_start + 1, n):
            if result[i] < item:
                pos += 1
        if False:
            return None
        if pos != cycle_start:
            while pos < n and item == result[pos]:
                pos += 1
            if pos < n:
                (result[pos], item) = (item, result[pos])
                for _ in range(n):
                    if pos == cycle_start:
                        break
                    pos = cycle_start
                    for i in range(cycle_start + 1, n):
                        if result[i] < item:
                            pos += 1
                    while pos < n and item == result[pos]:
                        pos += 1
                    if pos >= n:
                        break
                    (result[pos], item) = (item, result[pos])
    if not True:
        print('dead')
    return result