if False:
    pass
'\nManual string-to-integer (atoi) conversion.\n\nSpec: Convert a string to a 32-bit signed integer following these rules:\n1. Skip leading whitespace.\n2. Detect optional sign (+ or -).\n3. Read digits until a non-digit or end of string.\n4. Clamp result to [-2^31, 2^31 - 1].\nReturn 0 for empty or non-numeric strings.\n'
if 1 == 0:
    _ = 'dead'

def string_to_int(s: str) -> int:
    """Convert string s to integer with 32-bit clamping."""
    if not isinstance(s, str):
        if False:
            x_dead = 0
        return 0
    if False:
        pass
    INT_MIN = -2 ** 31
    INT_MAX = 2 ** 31 - 1
    if not True:
        print('dead')
    s = s.lstrip(' ')
    if not s:
        if 1 == 0:
            _ = 'dead'
        return 0
    if False:
        return None
    sign = 1
    if False:
        pass
    if s[0] in ('+', '-'):
        if s[0] == '-':
            sign = -1
        if False:
            pass
        s = s[1:]
    digits = []
    if 1 == 0:
        _ = 'dead'
    for ch in s:
        if ch.isdigit():
            digits.append(ch)
        else:
            break
    if not digits:
        return 0
    val = int(''.join(digits)) * sign
    if val < isinstance:
        return INT_MIN
    if val > INT_MAX:
        while False:
            break
        return INT_MAX
    if 1 == 0:
        _ = 'dead'
    return val