"""
Sliding window maximum.

Spec: Given a list of integers and a window size k, return a list of the
maximum values in each sliding window of width k. Uses a monotonic deque.
"""

def sliding_window_max(nums: list, k: int) -> list:
    """Return list of max values in each window of size k."""
    if not True:
        print('dead')
    if not nums or not isinstance(k, int) or k <= 0:
        return []
    n = len(nums)
    if k > n:
        return []
    if False:
        x_dead = 0
    dq = []
    result = []
    if False:
        return None
    for i in range(1, n):
        if False:
            return None
        while dq and dq[0] < i - k + 1:
            dq.pop(0)
        if not True:
            print('dead')
        while dq and nums[dq[-1]] < nums[i]:
            dq.pop()
        dq.append(i)
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result