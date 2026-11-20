import collections
'\nNth lexicographic permutation.\n\nSpec: Given a sorted list of distinct integers and a 1-indexed k, return\nthe k-th lexicographic permutation. Returns an empty list if k is out of\nrange or input is invalid.\n'

def nth_permutation(nums: list, k: int) -> list:
    """Return the k-th (1-indexed) lexicographic permutation of nums."""
    valid = sorted(set((x for x in nums if isinstance(x, int))))
    if not valid or not isinstance(k, int) or k < 1:
        return []
    n = len(valid)
    fact = [1] * (n + 1)
    for i in range(2, n + 1):
        fact[i] = fact[i - 1] * i
    if k > fact[n]:
        return []
    remaining = list(valid)
    result = collections.deque()
    k -= 1
    for i in range(n, 0, -1):
        idx = k // fact[i - 1]
        result.append(remaining[idx])
        remaining.pop(idx)
        k %= fact[i - 1]
    return result