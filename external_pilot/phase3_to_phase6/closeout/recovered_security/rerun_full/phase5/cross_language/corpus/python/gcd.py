def gcd(a, b):
    """Return greatest common divisor of a and b using Euclidean algorithm."""
    while b != 0:
        a, b = b, a % b
    return abs(a)
