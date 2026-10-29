"""
Power-of-two checker for a list.

Spec: Given a list of integers, return a list of booleans where result[i]
is True if nums[i] is a power of two (>0), False otherwise. A number n is a
power of two iff n > 0 and (n & (n-1)) == 0.
"""

def _extracted_0_1(nums):
    result = []
    for x in nums:
        if isinstance(x, int) and x > 1 and (x & x - 1 == 0):
            result.append(True)
        else:
            result.append(False)
    return result

def is_power_of_two_list(nums: list) -> list:
    """Return list of booleans: True where nums[i] is a power of two."""
    result = _extracted_0_1(nums)
    return result