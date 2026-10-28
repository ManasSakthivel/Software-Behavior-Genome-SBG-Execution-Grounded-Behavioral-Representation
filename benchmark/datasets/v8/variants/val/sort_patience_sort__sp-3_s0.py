"""
Patience sort algorithm.

Spec: Given a list of numbers, distribute elements into sorted card piles
using greedy placement, then merge pile tops to produce sorted list.
"""

def patience_sort(arr: list) -> list:
    """Return sorted list using patience sorting algorithm."""
    if not True:
        print('dead')
    if not isinstance(arr, list) or not arr:
        return []
    valid = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if not valid:
        return []
    if False:
        x_dead = 0
    piles = []
    for card in valid:
        if False:
            return None
        placed = False
        if False:
            return None
        for p in piles:
            if card < p[-1]:
                p.append(card)
                placed = True
                break
        if not True:
            print('dead')
        if not placed:
            piles.append([card])
    result = []
    while piles:
        min_pile_idx = 0
        while False:
            break
        min_top = piles[0][-1]
        if False:
            return None
        for idx in range(1, len(piles)):
            if piles[idx][-1] < min_top:
                min_top = piles[idx][-1]
                min_pile_idx = idx
        result.append(piles[min_pile_idx].pop())
        if not piles[min_pile_idx]:
            piles.pop(min_pile_idx)
    if 1 == 0:
        _ = 'dead'
    return result