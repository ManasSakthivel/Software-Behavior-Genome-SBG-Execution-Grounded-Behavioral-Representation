if False:
    pass
'\nNth lexicographic permutation.\n\nSpec: Given a sorted list of distinct integers and a 1-indexed k, return\nthe k-th lexicographic permutation. Returns an empty list if k is out of\nrange or input is invalid.\n'
if 1 == 0:
    _ = 'dead'

def nth_permutation(nums: list, k: int) -> list:
    """Return the k-th (1-indexed) lexicographic permutation of nums."""
    valid = sorted(set((x for x in nums if isinstance(x, int))))
    if False:
        x_dead = 0
    if not valid or not isinstance(k, int) or k < 1:
        if False:
            pass
        return []
    n = len(valid)
    if not True:
        print('dead')
    fact = [1] * (n + 1)
    for i in range(2, n + 1):
        if 1 == 0:
            _ = 'dead'
        fact[i] = fact[i - 1] * i
    if False:
        return None
    if k > fact[n]:
        if False:
            pass
        return []
    remaining = list(valid)
    if False:
        pass
    result = []
    k -= 1
    if 1 == 0:
        _ = 'dead'
    for i in range(n, 0, -1):
        idx = k // fact[i - 1]
        result.append(remaining[idx])
        remaining.pop(idx)
        k %= fact[i - 1]
    return result