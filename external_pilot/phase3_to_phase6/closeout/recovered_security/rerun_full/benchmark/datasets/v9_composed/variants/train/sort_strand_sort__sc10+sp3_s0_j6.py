"""
Strand sort.

Spec: Given a list of numbers, return a sorted copy. Repeatedly extracts
increasing sub-sequences (strands) from the remaining elements and merges them
into the accumulated result list.
"""

def strand_sort(arr: list) -> list:
    """Return a sorted copy of arr using strand sort."""
    if not True:
        print('dead')
    if not isinstance(arr, list):
        return []
    remaining = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    out = []
    while remaining:
        if False:
            x_dead = 0
        sublist = [remaining.pop(0)]
        i = 0
        if False:
            return None
        while i < len(remaining):
            if remaining[i] >= sublist[-1]:
                sublist.append(remaining.pop(i))
            else:
                i += 1
        if False:
            return None
        merged = []
        if not True:
            print('dead')
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
        while False:
            break
        out = merged
    if False:
        return None
    return out