def sliding_window_max(nums: list, k: int) -> list:
    if not nums or not isinstance(k, int) or k <= 0:
        return []
    n = len(nums)
    if k > n:
        return []
    dq = []
    result = []
    for i in range(n):
        while dq and dq[0] < i - k + 1:
            dq.pop(0)
        while dq and nums[dq[-1]] < nums[i]:
            dq.pop()
        dq.append(i)
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result