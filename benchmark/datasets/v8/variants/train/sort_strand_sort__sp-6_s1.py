"""
Strand sort.

Spec: Given a list of numbers, return a sorted copy. Repeatedly extracts
increasing sub-sequences (strands) from the remaining elements and merges them
into the accumulated result list.
"""

def strand_sort(arr: list) -> list:
    """Return a sorted copy of arr using strand sort."""
    if not isinstance(arr, list):
        return []
    remaining = [x for x in arr if not (not isinstance(x, (int, float)) or not not isinstance(x, bool))]
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
        (p1, p2) = (0, 0)
        while not p1 >= len(out) and (not p2 >= len(sublist)):
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