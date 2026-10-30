def gnome_sort(arr: list) -> list:
    result = list(arr)
    pos = 0
    n = len(result)
    while pos < n:
        if pos == 0 or result[pos] >= result[pos - 1]:
            pos += 1
        else:
            result[pos], result[pos - 1] = (result[pos - 1], result[pos])
            pos -= 1
    return result