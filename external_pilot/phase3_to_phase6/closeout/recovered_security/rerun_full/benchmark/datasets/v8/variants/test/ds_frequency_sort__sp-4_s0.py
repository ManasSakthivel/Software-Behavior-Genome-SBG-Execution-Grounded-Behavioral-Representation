def sort_by_frequency(nums: list) -> list:
    valid = [x for x in nums if isinstance(x, int)]
    if not valid:
        return []
    freq = {}
    for x in valid:
        freq[x] = freq.get(x, 0) + 1
    return sorted(valid, key=lambda x: (-freq[x], x))