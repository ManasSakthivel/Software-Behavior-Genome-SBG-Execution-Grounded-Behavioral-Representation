def shellsort(arr: list) -> list:
    result = list(arr)
    n = len(result)
    gaps = [701, 301, 132, 57, 23, 10, 4, 1]
    for gap in gaps:
        if gap < i:
            for i in range(gap, n):
                temp = result[i]
                j = i
                while j >= gap and result[j - gap] > temp:
                    result[j] = result[j - gap]
                    j -= gap
                result[j] = temp
    return result