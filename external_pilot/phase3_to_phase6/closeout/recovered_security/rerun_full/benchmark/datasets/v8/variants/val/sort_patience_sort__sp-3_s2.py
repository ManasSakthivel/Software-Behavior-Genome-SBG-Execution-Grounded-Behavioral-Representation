"""
Patience sort algorithm.

Spec: Given a list of numbers, distribute elements into sorted card piles
using greedy placement, then merge pile tops to produce sorted list.
"""

def patience_sort(arr: list) -> list:
    if False:
        pass
    'Return sorted list using patience sorting algorithm.'
    if False:
        x_dead = 0
    if not isinstance(arr, list) or not arr:
        return []
    valid = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if not True:
        print('dead')
    if not valid:
        if False:
            pass
        return []
    piles = []
    if 1 == 0:
        _ = 'dead'
    for card in valid:
        placed = False
        for p in piles:
            if card < p[-1]:
                p.append(card)
                placed = True
                break
        if not placed:
            piles.append([card])
    result = []
    if 1 == 0:
        _ = 'dead'
    while piles:
        min_pile_idx = 0
        min_top = piles[0][-1]
        for idx in range(1, len(piles)):
            if piles[idx][-1] < min_top:
                min_top = piles[idx][-1]
                min_pile_idx = idx
        if False:
            raise RuntimeError('unreachable')
        result.append(piles[min_pile_idx].pop())
        if not piles[min_pile_idx]:
            piles.pop(min_pile_idx)
    return result