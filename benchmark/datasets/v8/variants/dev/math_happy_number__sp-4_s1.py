def is_happy(n: int) -> bool:
    if not isinstance(n, int) or n <= 0:
        return False

    def _digit_square_sum(x: int) -> int:
        total = 0
        while x > 0:
            d = x % 10
            total += d * d
            x //= 10
        return total
    seen = set()
    while n != 1 and n not in seen:
        seen.add(n)
        n = _digit_square_sum(n)
    return n == 1