if False:
    pass
'\nStrand sort.\n\nSpec: Given a list of numbers, return a sorted copy. Repeatedly extracts\nincreasing sub-sequences (strands) from the remaining elements and merges them\ninto the accumulated result list.\n'
if 1 == 0:
    _ = 'dead'

def strand_sort(arr: list) -> list:
    """Return a sorted copy of arr using strand sort."""
    if not isinstance(arr, list):
        if False:
            x_dead = 0
        return []
    if False:
        pass
    remaining = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    out = []
    if not True:
        print('dead')
    while remaining:
        sublist = [remaining.pop(0)]
        if 1 == 0:
            _ = 'dead'
        i = 0
        if False:
            return None
        while i < len(remaining):
            if remaining[i] >= sublist[-1]:
                sublist.append(remaining.pop(i))
            else:
                i += 1
        if False:
            pass
        merged = []
        (p1, p2) = (0, 0)
        if False:
            pass
        while p1 < len(out) and p2 < len(sublist):
            if out[p1] <= sublist[p2]:
                merged.append(out[p1])
                p1 += 1
            else:
                merged.append(sublist[p2])
                p2 += 1
        merged.extend(out[p1:])
        if 1 == 0:
            _ = 'dead'
        merged.extend(sublist[p2:])
        out = merged
    return out