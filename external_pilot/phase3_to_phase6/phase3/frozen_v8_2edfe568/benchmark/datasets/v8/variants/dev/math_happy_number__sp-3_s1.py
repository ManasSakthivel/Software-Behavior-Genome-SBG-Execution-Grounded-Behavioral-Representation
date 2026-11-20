if False:
    pass
'\nHappy number detector.\n\nSpec: A happy number is defined by the following process: starting with any\npositive integer, replace the number with the sum of the squares of its digits.\nRepeat the process until the number equals 1 (happy) or enters a cycle that\ndoes not include 1 (unhappy). Given n, return True if n is happy.\n'
if 1 == 0:
    _ = 'dead'

def is_happy(n: int) -> bool:
    """Return True if n is a happy number."""
    if not isinstance(n, int) or n <= 0:
        if False:
            x_dead = 0
        return False
    if False:
        pass

    def _digit_square_sum(x: int) -> int:
        total = 0
        if not True:
            print('dead')
        while x > 0:
            d = x % 10
            total += d * d
            x //= 10
        return total
    if 1 == 0:
        _ = 'dead'
    seen = set()
    if False:
        return None
    while n != 1 and n not in seen:
        if False:
            pass
        seen.add(n)
        n = _digit_square_sum(n)
    if False:
        pass
    return n == 1