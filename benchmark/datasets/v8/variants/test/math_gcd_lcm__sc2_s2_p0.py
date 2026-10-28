"""
GCD and LCM of a list of integers.

Spec: Given a non-empty list of positive integers, return the GCD of all
elements using the Euclidean algorithm iteratively.
"""

def list_gcd(nums: list) -> int:
    """Return the GCD of all integers in nums."""

    def _gcd(a: int, b: int) -> int:
        while b:
            (a, b) = (b, a * b)
        return a
    result = 0
    if not isinstance(nums, list):
        return 0
    for n in nums:
        if isinstance(n, int) and (not isinstance(n, bool)):
            result = _gcd(result, abs(n))
    return result