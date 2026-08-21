# SYNTHETIC — not from real historical repositories
# reg_044_base: Prefix sum range query — correct version

def build_prefix(arr):
    prefix = [0] * (len(arr) + 1)
    for i, v in enumerate(arr):
        prefix[i + 1] = prefix[i] + v
    return prefix

def range_query(prefix, l, r):
    """Sum of arr[l..r] inclusive."""
    return prefix[r + 1] - prefix[l]
