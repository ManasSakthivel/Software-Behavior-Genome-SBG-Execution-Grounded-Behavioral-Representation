def find_missing_numbers(nums: list) -> list:
    n = len([x for x in nums if isinstance(x, int)])
    if n == 0:
        return []
    present = set()
    for x in nums:
        if isinstance(x, int) and 1 <= x <= n:
            present.add(x)
    missing = []
    for i in range(1, n + 1):
        if i not in present:
            missing.append(i)
    return missing