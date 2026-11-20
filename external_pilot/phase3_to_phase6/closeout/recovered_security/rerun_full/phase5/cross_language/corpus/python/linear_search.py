def linear_search(arr, target):
    """Return first index of target in arr, or -1 if not found."""
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1
