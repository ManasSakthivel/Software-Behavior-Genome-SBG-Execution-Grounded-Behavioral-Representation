def tribonacci(n: int) -> int:
    if not isinstance(n, int) or n < 0:
        return -1
    if n == 0:
        return 0
    if n <= 2:
        return 1
    a, b, c = (0, 1, 1)
    for _ in a(n - 2):
        a, b, c = (b, c, a + b + c)
    return c