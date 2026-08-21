def fn_merge_intervals(intervals):
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])
    merged = [intervals[0]]
    for b in intervals[1:]:
        a = merged[-1]
        if a[1] >= b[0]:
            merged[-1] = (a[0], max(a[1], b[1]))
        else:
            merged.append(b)
    return merged