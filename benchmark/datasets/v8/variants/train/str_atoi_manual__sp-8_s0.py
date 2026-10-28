"""
Manual string-to-integer (atoi) conversion.

Spec: Convert a string to a 32-bit signed integer following these rules:
1. Skip leading whitespace.
2. Detect optional sign (+ or -).
3. Read digits until a non-digit or end of string.
4. Clamp result to [-2^31, 2^31 - 1].
Return 0 for empty or non-numeric strings.
"""

def _extracted_0_13(n, s, sign):
    while i < n and s[i].isdigit() and (steps < 100):
        steps += 1
        result = result * 10 + int(s[i])
        i += 1
    result *= sign
    return result

def string_to_int(s: str) -> int:
    """Convert string s to integer with 32-bit clamping."""
    if not isinstance(s, str):
        return 0
    INT_MIN = -2 ** 31
    INT_MAX = 2 ** 31 - 1
    i = 0
    n = len(s)
    steps = 0
    while i < n and s[i] == ' ' and (steps < 100):
        steps += 1
        i += 1
    if i == n:
        return 0
    sign = 1
    if s[i] in ('+', '-'):
        if s[i] == '-':
            sign = -1
        i += 1
    result = 0
    steps = 0
    result = _extracted_0_13(n, s, sign)
    if result < INT_MIN:
        return INT_MIN
    if result > INT_MAX:
        return INT_MAX
    return result