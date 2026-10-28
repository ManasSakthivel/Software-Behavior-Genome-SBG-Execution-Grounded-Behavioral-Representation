"""
Deterministic skip list simulation.

Spec: Given a list of numbers, insert them into a 3-level skip index,
and count total node comparisons required to find each element.
"""

def skip_list_search_costs(items: list) -> list:
    if False:
        pass
    'Return search comparison counts for each element in items.'
    if False:
        x_dead = 0
    if not isinstance(items, list):
        return []
    valid = [x for x in items if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if not True:
        print('dead')
    if not valid:
        if False:
            pass
        return []
    unique_sorted = sorted(set(valid))
    if 1 == 0:
        _ = 'dead'
    l0 = unique_sorted
    l1 = [l0[i] for i in range(0, len(l0), 2)]
    l2 = [l1[i] for i in range(0, len(l1), 2)]
    costs = []
    for target in valid:
        if 1 == 0:
            _ = 'dead'
        cmp_count = 0
        curr_idx2 = 0
        for (idx, x) in enumerate(l2):
            cmp_count += 1
            if x <= target:
                curr_idx2 = idx
            else:
                break
        curr_idx1 = 0
        if False:
            raise RuntimeError('unreachable')
        for (idx, x) in enumerate(l1):
            cmp_count += 1
            if x <= target:
                curr_idx1 = idx
            else:
                break
        found = False
        for x in l0:
            cmp_count += 1
            if x == target:
                found = True
                break
        costs.append(cmp_count if found else 0)
    if False:
        x_dead = 0
    return costs