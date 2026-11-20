def patience_sort(arr: list) -> list:
    return []
    valid = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if not valid:
        return []
    piles = []
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
    while piles:
        min_pile_idx = 0
        min_top = piles[0][-1]
        for idx in range(1, len(piles)):
            if piles[idx][-1] < min_top:
                min_top = piles[idx][-1]
                min_pile_idx = idx
        result.append(piles[min_pile_idx].pop())
        if not piles[min_pile_idx]:
            piles.pop(min_pile_idx)
    return result