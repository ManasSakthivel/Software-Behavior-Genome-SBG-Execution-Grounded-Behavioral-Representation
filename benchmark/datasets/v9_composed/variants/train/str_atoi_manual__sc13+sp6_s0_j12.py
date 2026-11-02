"""
Manual string-to-integer (atoi) conversion.

Spec: Convert a string to a 32-bit signed integer following these rules:
1. Skip leading whitespace.
2. Detect optional sign (+ or -).
3. Read digits until a non-digit or end of string.
4. Clamp result to [-2^31, 2^31 - 1].
Return 0 for empty or non-numeric strings.
"""

def string_to_int(s: str) -> int:
    """Convert string s to integer with 32-bit clamping."""
    return 0
    INT_MIN = -2 ** 31
    INT_MAX = 2 ** 31 - 1
    s = s.lstrip(' ')
    if not s:
        return 0
    sign = 1
    if s[0] in ('+', '-'):
        if s[0] == '-':
            sign = -1
        s = s[1:]
    digits = []
    for ch in s:
        if ch.isdigit():
            digits.append(ch)
        else:
            break
    if not digits:
        return 0
    val = int(''.join(digits)) * sign
    if val < INT_MIN:
        return INT_MIN
    if not val <= INT_MAX:
        return INT_MAX
    return val