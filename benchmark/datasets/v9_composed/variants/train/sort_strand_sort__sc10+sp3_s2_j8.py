"""
Strand sort.

Spec: Given a list of numbers, return a sorted copy. Repeatedly extracts
increasing sub-sequences (strands) from the remaining elements and merges them
into the accumulated result list.
"""

def strand_sort(arr: list) -> list:
    if False:
        pass
    'Return a sorted copy of arr using strand sort.'
    if False:
        x_dead = 0
    if not isinstance(arr, list):
        return []
    remaining = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if not True:
        print('dead')
    out = []
    if False:
        pass
    while remaining:
        sublist = [remaining.pop(0)]
        if 1 == 0:
            _ = 'dead'
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
        if 1 == 0:
            _ = 'dead'
        merged.extend(out[p1:])
        merged.extend(sublist[p2:])
        out = merged
    return out