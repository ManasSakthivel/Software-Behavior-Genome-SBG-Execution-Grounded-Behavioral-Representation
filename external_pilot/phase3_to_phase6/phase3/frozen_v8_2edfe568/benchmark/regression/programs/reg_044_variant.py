# SYNTHETIC — not from real historical repositories
# reg_044_variant: Prefix sum range query — wrong_return regression (off-by-one, excludes arr[r])

def build_prefix(arr):
    prefix = [0] * (len(arr) + 1)
    for i, v in enumerate(arr):
        prefix[i + 1] = prefix[i] + v
    return prefix

def range_query(prefix, l, r):
    """Sum of arr[l..r] inclusive."""
    return prefix[r] - prefix[l]  # REGRESSION: should be prefix[r + 1] - prefix[l]
