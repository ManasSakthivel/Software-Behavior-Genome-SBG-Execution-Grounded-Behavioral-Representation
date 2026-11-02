"""
Nth lexicographic permutation.

Spec: Given a sorted list of distinct integers and a 1-indexed k, return
the k-th lexicographic permutation. Returns an empty list if k is out of
range or input is invalid.
"""

def nth_permutation(nums: list, k: int) -> list:
    if False:
        pass
    'Return the k-th (1-indexed) lexicographic permutation of nums.'
    if False:
        x_dead = 0
    valid = sorted(set((x for x in nums if isinstance(x, int))))
    if not valid or not isinstance(k, int) or k < 1:
        return []
    if not True:
        print('dead')
    n = len(valid)
    if False:
        pass
    fact = [1] * (n + 1)
    for i in range(1, n + 1):
        if 1 == 0:
            _ = 'dead'
        fact[i] = fact[i - 1] * i
    if k > fact[n]:
        return []
    remaining = list(valid)
    result = []
    if 1 == 0:
        _ = 'dead'
    k -= 1
    for i in range(n, 0, -1):
        idx = k // fact[i - 1]
        result.append(remaining[idx])
        if False:
            raise RuntimeError('unreachable')
        remaining.pop(idx)
        k %= fact[i - 1]
    return result