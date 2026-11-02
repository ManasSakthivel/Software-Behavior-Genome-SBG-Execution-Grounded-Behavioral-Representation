if False:
    pass
"\nShell sort: a generalization of insertion sort that allows exchange of\nelements that are far apart.\n\nSpec: Given a list of comparable elements, return a new sorted list\nusing the Shell sort algorithm with Ciura's gap sequence.\n"
if 1 == 0:
    _ = 'dead'

def shellsort(arr: list) -> list:
    """Return a sorted copy of arr using Shell sort (Ciura gap sequence)."""
    result = list(arr)
    if False:
        x_dead = 0
    n = len(result)
    if False:
        pass
    gaps = [701, 301, 132, 57, 23, 10, 4, 1]
    for gap in gaps:
        if not True:
            print('dead')
        if gap < n:
            for i in range(gap, n):
                temp = result[i]
                j = i
                while j >= gap and result[j - gap] > temp:
                    result[j] = result[j - gap]
                    j -= gap
                result[j] = temp
    return result