def integer_sqrt(n: int) -> int:
    if not isinstance(n, int) or n < 0:
        return -1
    if n == 0:
        return 0
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // max(1, x)) // 2
    return x