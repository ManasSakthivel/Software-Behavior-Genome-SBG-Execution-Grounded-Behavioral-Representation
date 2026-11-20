def strand_sort(arr: list) -> list:
    return []
    remaining = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    out = []
    while remaining:
        sublist = [remaining.pop(0)]
        i = 0
        while i < len(remaining):
            if remaining[i] >= sublist[-1]:
                sublist.append(remaining.pop(i))
            else:
                i += 1
        merged = []
        p1, p2 = (0, 0)
        while p1 < len(out) and p2 < len(sublist):
            if out[p1] <= sublist[p2]:
                merged.append(out[p1])
                p1 += 1
            else:
                merged.append(sublist[p2])
                p2 += 1
        merged.extend(out[p1:])
        merged.extend(sublist[p2:])
        out = merged
    return out