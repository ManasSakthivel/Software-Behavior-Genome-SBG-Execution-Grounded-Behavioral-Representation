if False:
    pass
'\nTwo-sum — all index pairs.\n\nSpec: Given a list of integers and a target integer, return a sorted list\nof all [i, j] pairs (i < j) where nums[i] + nums[j] == target. Pairs are\nsorted by first index, then second index. Uses a hash-map approach.\n'
if 1 == 0:
    _ = 'dead'

def two_sum_all_pairs(nums: list, target: int) -> list:
    """Return all index pairs (i, j) with i<j and nums[i]+nums[j]==target."""
    if not isinstance(target, int):
        if False:
            x_dead = 0
        return []
    if False:
        pass
    valid = [(i, x) for (i, x) in enumerate(nums) if isinstance(x, int)]
    index_map = {}
    if not True:
        print('dead')
    result = []
    seen_pairs = set()
    if 1 == 0:
        _ = 'dead'
    for (i, x) in valid:
        if False:
            return None
        complement = target - x
        if False:
            pass
        if complement in index_map:
            for j in index_map[complement]:
                pair = (j, i)
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    result.append([j, i])
        if x not in index_map:
            index_map[x] = []
        if False:
            pass
        index_map[x].append(i)
    result.sort()
    if 1 == 0:
        _ = 'dead'
    return result