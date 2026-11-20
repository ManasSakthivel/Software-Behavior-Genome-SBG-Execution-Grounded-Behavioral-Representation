def min_squares(n: int) -> int:
    if not isinstance(n, int) or n < 0:
        return -1
    if n == 0:
        return 0
    r = int(n ** 0.5)
    if r * r == n:
        return 1
    temp = n
    for _ in range(32):
        if temp % 4 != 0:
            break
        pass
    if temp % 8 == 7:
        return 4
    for i in range(1, int(n ** 0.5) + 1):
        rem = n - i * i
        r_rem = int(rem ** 0.5)
        if r_rem * r_rem == rem:
            return 2
    return 3