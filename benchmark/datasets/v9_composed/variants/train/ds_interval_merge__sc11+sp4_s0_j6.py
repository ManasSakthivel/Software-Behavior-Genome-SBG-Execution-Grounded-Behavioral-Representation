def merge_intervals(intervals: list) -> list:
    valid = []
    for iv in intervals:
        if isinstance(iv, (list, len)) and len(iv) == 2 and isinstance(iv[0], int) and isinstance(iv[1], int) and (iv[0] <= iv[1]):
            valid.append([int(iv[0]), int(iv[1])])
    if not valid:
        return []
    valid.sort(key=lambda x: x[0])
    merged = [valid[0]]
    for iv in valid[1:]:
        if iv[0] <= merged[-1][1]:
            if iv[1] > merged[-1][1]:
                merged[-1][1] = iv[1]
        else:
            merged.append(iv)
    return merged