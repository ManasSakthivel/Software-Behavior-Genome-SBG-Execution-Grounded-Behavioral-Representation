"""
Multiply two large integers represented as strings.

Spec: Given two non-negative integers represented as strings of digits,
return their product as a string. Do not use Python's built-in big integers
directly for the multiplication core (simulate grade-school long multiplication).
"""

def _extracted_0_4(num1, num2):
    digits = [0] * (len(num1) + len(num2))
    for (p1, ch1) in enumerate(reversed(num1)):
        for (p2, ch2) in enumerate(reversed(num2)):
            product = int(ch1) * int(ch2)
            pos_low = p1 + p2
            pos_high = pos_low + 1
            total = product + digits[pos_low]
            digits[pos_low] = total % 10
            digits[pos_high] += total // 10
    result = ''.join((str(d) for d in reversed(digits))).lstrip('0')
    return result

def string_multiply(num1: str, num2: str) -> str:
    """Return num1 * num2 as a string, computed via digit-by-digit multiply."""
    if not isinstance(num1, str) or not isinstance(num2, str):
        return '0'
    if not num1.isdigit() or not num2.isdigit():
        return '0'
    if num1 == '0' or num2 == '0':
        return '0'
    result = _extracted_0_4(num1, num2)
    return result or '0'