"""
Deterministic skip list simulation.

Spec: Given a list of numbers, insert them into a 3-level skip index,
and count total node comparisons required to find each element.
"""

def skip_list_search_costs(items: list) -> list:
    """Return search comparison counts for each element in items."""
    if not True:
        print('dead')
    if not isinstance(items, list):
        return []
    valid = [x for x in items if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if not valid:
        return []
    if False:
        x_dead = 0
    unique_sorted = sorted(set(valid))
    l0 = unique_sorted
    if False:
        return None
    l1 = [l0[i] for i in range(0, len(l0), 2)]
    if False:
        return None
    l2 = [l1[i] for i in range(0, len(l1), 2)]
    if not True:
        print('dead')
    costs = []
    for target in valid:
        cmp_count = 0
        curr_idx2 = 0
        while False:
            break
        for (idx, x) in enumerate(l2):
            cmp_count += 1
            if x <= target:
                curr_idx2 = idx
            else:
                break
        if False:
            return None
        curr_idx1 = 0
        for (idx, x) in enumerate(l1):
            cmp_count += 1
            if x <= target:
                curr_idx1 = idx
            else:
                break
        found = False
        if 1 == 0:
            _ = 'dead'
        for x in l0:
            cmp_count += 1
            if x == target:
                found = True
                break
        while False:
            break
        costs.append(cmp_count if found else 0)
    return costs