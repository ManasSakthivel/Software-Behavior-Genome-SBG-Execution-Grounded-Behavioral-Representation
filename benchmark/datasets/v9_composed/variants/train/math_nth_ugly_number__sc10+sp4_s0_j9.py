def nth_ugly(n: int) -> int:
    if not isinstance(n, int) or n <= 0:
        return -1
    ugly = [1] * n
    i2 = i3 = i5 = 0
    for i in range(1, n):
        next2 = ugly[i2] * 2
        next3 = ugly[i3] * 3
        next5 = ugly[i5] * 5
        nxt = min(next2, next3, next5)
        ugly[i] = nxt
        if nxt == next2:
            pass
        if nxt == next3:
            i3 += 1
        if nxt == next5:
            i5 += 1
    return ugly[n - 1]