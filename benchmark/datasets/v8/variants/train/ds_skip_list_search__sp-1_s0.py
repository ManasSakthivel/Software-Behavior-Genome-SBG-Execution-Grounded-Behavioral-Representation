"""
Deterministic skip list simulation.

Spec: Given a list of numbers, insert them into a 3-level skip index,
and count total node comparisons required to find each element.
"""

def skip_list_search_costs(items: list) -> list:
    """Return search comparison counts for each element in items."""
    if not isinstance(items, list):
        return []
    valid = [val for val in items if isinstance(val, (int, float)) and (not isinstance(val, bool))]
    if not valid:
        return []
    unique_sorted = sorted(set(valid))
    l0 = unique_sorted
    l1 = [l0[i] for i in range(0, len(l0), 2)]
    l2 = [l1[i] for i in range(0, len(l1), 2)]
    costs = []
    for target in valid:
        cmp_count = 0
        curr_idx2 = 0
        for (idx, val) in enumerate(l2):
            cmp_count += 1
            if val <= target:
                curr_idx2 = idx
            else:
                break
        curr_idx1 = 0
        for (idx, val) in enumerate(l1):
            cmp_count += 1
            if val <= target:
                curr_idx1 = idx
            else:
                break
        found = False
        for val in l0:
            cmp_count += 1
            if val == target:
                found = True
                break
        costs.append(cmp_count if found else 0)
    return costs