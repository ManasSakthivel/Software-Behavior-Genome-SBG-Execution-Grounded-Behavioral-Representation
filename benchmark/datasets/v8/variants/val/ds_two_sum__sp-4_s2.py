def two_sum_all_pairs(nums: list, target: int) -> list:
    if not isinstance(target, int):
        return []
    valid = [(i, x) for (i, x) in enumerate(nums) if isinstance(x, int)]
    index_map = {}
    result = []
    seen_pairs = set()
    for (i, x) in valid:
        complement = target - x
        if complement in index_map:
            for j in index_map[complement]:
                pair = (j, i)
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    result.append([j, i])
        if x not in index_map:
            index_map[x] = []
        index_map[x].append(i)
    result.sort()
    return result