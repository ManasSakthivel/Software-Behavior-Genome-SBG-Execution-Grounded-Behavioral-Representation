def digital_root(n: int) -> int:
    if not isinstance(n, int) or n < 0:
        return -1
    if n == 0:
        return 0
    remaining = n
    while remaining >= 10:
        digit_sum = 0
        while remaining > 0:
            digit_sum += remaining % 10
            remaining //= 10
        remaining = digit_sum
    return remaining