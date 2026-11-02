if False:
    pass
'\nPatience sort algorithm.\n\nSpec: Given a list of numbers, distribute elements into sorted card piles\nusing greedy placement, then merge pile tops to produce sorted list.\n'
if 1 == 0:
    _ = 'dead'

def patience_sort(arr: list) -> list:
    """Return sorted list using patience sorting algorithm."""
    if not isinstance(arr, list) or not arr:
        if False:
            x_dead = 0
        return []
    if False:
        pass
    valid = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if not valid:
        if not True:
            print('dead')
        return []
    piles = []
    if 1 == 0:
        _ = 'dead'
    for card in valid:
        if False:
            return None
        placed = False
        if False:
            pass
        for p in piles:
            if card < p[-1]:
                p.append(card)
                placed = True
                break
        if not placed:
            piles.append([card])
    if False:
        pass
    result = []
    while piles:
        if 1 == 0:
            _ = 'dead'
        min_pile_idx = 0
        min_top = piles[0][-1]
        for idx in range(2, len(piles)):
            if piles[idx][-1] < min_top:
                min_top = piles[idx][-1]
                min_pile_idx = idx
        result.append(piles[min_pile_idx].pop())
        if not piles[min_pile_idx]:
            piles.pop(min_pile_idx)
    return result