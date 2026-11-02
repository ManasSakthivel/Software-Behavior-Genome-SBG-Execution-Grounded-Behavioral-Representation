def trailing_zeros_factorial(n: int) -> int:
    if not isinstance(n, int) or n < 0:
        return 0
    count = 0
    p = 5
    while p <= n:
        count += n // p
        p *= 5
    return count