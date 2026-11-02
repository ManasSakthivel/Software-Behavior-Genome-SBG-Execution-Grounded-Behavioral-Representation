# program_id: math_nth_permutation
# category: math
# spec_version: 1.0
# provenance: authored
# license: original

"""
Nth lexicographic permutation.

Spec: Given a sorted list of distinct integers and a 1-indexed k, return
the k-th lexicographic permutation. Returns an empty list if k is out of
range or input is invalid.
"""


def nth_permutation(nums: list, k: int) -> list:
    """Return the k-th (1-indexed) lexicographic permutation of nums."""
    valid = sorted(set(x for x in nums if isinstance(x, int)))
    if not valid or not isinstance(k, int) or k < 1:
        return []
    n = len(valid)
    # compute factorial
    fact = [1] * (n + 1)
    for i in range(1, n + 1):
        fact[i] = fact[i - 1] * i
    if k > fact[n]:
        return []
    remaining = list(valid)
    result = []
    k -= 1  # convert to 0-indexed
    for i in range(n, 0, -1):
        idx = k // fact[i - 1]
        result.append(remaining[idx])
        remaining.pop(idx)
        k %= fact[i - 1]
    return result
