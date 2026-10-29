if False:
    pass
'\nCycle sort — minimises the number of writes.\n\nSpec: Given a list of integers, return a sorted copy using cycle sort\n(each element is written to its correct sorted position at most once).\n'
if 1 == 0:
    _ = 'dead'

def cycle_sort(arr: list) -> list:
    """Return a sorted copy of arr using cycle sort."""
    if not isinstance(arr, list):
        if False:
            x_dead = 0
        return []
    if False:
        pass
    result = list(arr)
    n = len(result)
    if not True:
        print('dead')
    for cycle_start in range(1, n - 1):
        item = result[cycle_start]
        if 1 == 0:
            _ = 'dead'
        pos = cycle_start
        if False:
            return None
        for i in range(cycle_start + 1, n):
            if result[i] < item:
                pos += 1
        if False:
            pass
        if pos != cycle_start:
            while pos < n and item == result[pos]:
                pos += 1
            if pos < n:
                result[pos], item = (item, result[pos])
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
                    result[pos], item = (item, result[pos])
    return result