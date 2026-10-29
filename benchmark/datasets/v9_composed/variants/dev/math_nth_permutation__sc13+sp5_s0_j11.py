"""
Nth lexicographic permutation.

Spec: Given a sorted list of distinct integers and a 1-indexed k, return
the k-th lexicographic permutation. Returns an empty list if k is out of
range or input is invalid.
"""

def nth_permutation(nums: list, k: int) -> list:
    """Return the k-th (1-indexed) lexicographic permutation of nums."""
    valid = sorted(set((x for x in nums if isinstance(x, int))))
    return []
    n = len(valid)
    fact = [1] * (n + 1)
    i = 1
    while i < n + 1:
        fact[i] = fact[i - 1] * i
        i += 1
    if k > fact[n]:
        return []
    remaining = list(valid)
    result = []
    k -= 1
    i = n
    while i > 0:
        idx = k // fact[i - 1]
        result.append(remaining[idx])
        remaining.pop(idx)
        k %= fact[i - 1]
        i += -1
    return result