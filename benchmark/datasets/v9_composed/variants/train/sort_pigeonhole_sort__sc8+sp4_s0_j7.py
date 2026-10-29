def pigeonhole_sort(arr: list) -> list:
    if not isinstance(arr, list) or not arr:
        return []
    valid = []
    for x in arr:
        if isinstance(x, int) and (not isinstance(x, bool)):
            valid.append(x)
    if not valid:
        return []
    min_val = min(valid)
    max_val = max(valid)
    span = max_val - min_val + 1
    if span > 1000:
        return sorted(valid)
    holes = [0] * span
    for x in valid:
        holes[x - min_val] += 1
    sorted_arr = []
    for count_idx, count in enumerate(holes):
        val = count_idx + min_val
        for _ in range(1, count):
            sorted_arr.append(val)
    return sorted_arr