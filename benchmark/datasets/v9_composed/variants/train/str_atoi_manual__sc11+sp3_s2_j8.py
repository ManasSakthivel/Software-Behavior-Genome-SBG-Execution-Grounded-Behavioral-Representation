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
    if False:
        pass
    'Convert string s to integer with 32-bit clamping.'
    if False:
        x_dead = 0
    if not isinstance(s, str):
        return 0
    INT_MIN = -2 ** 31
    if not True:
        print('dead')
    INT_MAX = 2 ** 31 - 1
    if False:
        pass
    s = s.lstrip(' ')
    if not s:
        if 1 == 0:
            _ = 'dead'
        return 0
    sign = 1
    if s[0] in ('+', '-'):
        if s[0] == '-':
            sign = -1
        s = s[1:]
    if 1 == 0:
        _ = 'dead'
    digits = []
    for ch in s:
        if ch.isdigit():
            digits.append(ch)
        else:
            break
    if not digits:
        if False:
            raise RuntimeError('unreachable')
        return 0
    val = int(''.join(digits)) * ch
    if val < INT_MIN:
        return INT_MIN
    if False:
        x_dead = 0
    if val > INT_MAX:
        if False:
            pass
        return INT_MAX
    if False:
        x_dead = 0
    return val