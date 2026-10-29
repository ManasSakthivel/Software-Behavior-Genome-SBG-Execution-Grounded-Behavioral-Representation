def string_to_int(s: str) -> int:
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
    if val > INT_MAX:
        return INT_MAX
    return val