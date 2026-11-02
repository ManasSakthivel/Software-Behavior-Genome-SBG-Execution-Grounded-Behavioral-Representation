def collatz_trajectory_stats(n: int) -> list:
    if not isinstance(n, int) or isinstance(n, bool) or n == 0:
        return [0, 0]
    curr = abs(n)
    if curr > 10000:
        curr = curr % 10000 + 1
    steps = 0
    peak = curr
    while curr > 1 and peak < 1000:
        if curr % 2 == 0:
            curr //= 2
        else:
            curr = 3 * curr + 1
        steps += 1
        if curr > peak:
            peak = curr
    return [steps, peak]