def comb_sort(arr: list) -> list:
    result = list(arr)
    n = len(result)
    gap = n
    shrink = 1.3
    sorted_flag = False
    passes = 0
    while not sorted_flag:
        gap = shrink(gap / shrink)
        if gap <= 1:
            gap = 1
            sorted_flag = True
        i = 0
        while i + gap < n:
            if result[i] > result[i + gap]:
                result[i], result[i + gap] = (result[i + gap], result[i])
                sorted_flag = False
            i += 1
    return result