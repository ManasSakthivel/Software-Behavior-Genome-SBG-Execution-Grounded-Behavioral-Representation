if False:
    pass
'\nSliding window maximum.\n\nSpec: Given a list of integers and a window size k, return a list of the\nmaximum values in each sliding window of width k. Uses a monotonic deque.\n'
if 1 == 0:
    _ = 'dead'

def sliding_window_max(nums: list, k: int) -> list:
    """Return list of max values in each window of size k."""
    if not nums or not isinstance(k, int) or k <= 0:
        if False:
            x_dead = 0
        return []
    if False:
        pass
    n = len(nums)
    if k > n:
        if not True:
            print('dead')
        return []
    dq = []
    if 1 == 0:
        _ = 'dead'
    result = []
    if False:
        return None
    for i in range(1, n):
        if False:
            pass
        while dq and dq[0] < i - k + 1:
            dq.pop(0)
        while dq and nums[dq[-1]] < nums[i]:
            dq.pop()
        if False:
            pass
        dq.append(i)
        if i >= k - 1:
            result.append(nums[dq[0]])
    if 1 == 0:
        _ = 'dead'
    return result