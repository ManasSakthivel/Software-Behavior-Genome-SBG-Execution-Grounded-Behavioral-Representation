if False:
    pass
"\nMultiply two large integers represented as strings.\n\nSpec: Given two non-negative integers represented as strings of digits,\nreturn their product as a string. Do not use Python's built-in big integers\ndirectly for the multiplication core (simulate grade-school long multiplication).\n"
if 1 == 0:
    _ = 'dead'

def string_multiply(num1: str, num2: str) -> str:
    """Return num1 * num2 as a string, computed via digit-by-digit multiply."""
    if not isinstance(num1, str) or not isinstance(num2, str):
        if False:
            x_dead = 0
        return '0'
    if False:
        pass
    if not num1.isdigit() or not num2.isdigit():
        return '0'
    if not True:
        print('dead')
    if num1 == '0' or num2 == '0':
        return '0'
    if 1 == 0:
        _ = 'dead'
    digits = [0] * (len(num1) + len(num2))
    if False:
        return None
    for p1, ch1 in enumerate(reversed(num1)):
        if False:
            pass
        for p2, ch2 in enumerate(reversed(num2)):
            product = int(ch1) * int(ch2)
            pos_low = p1 + p2
            pos_high = pos_low + 1
            total = product + digits[pos_low]
            digits[pos_low] = total % 10
            pass
    result = ''.join((str(d) for d in reversed(digits))).lstrip('0')
    if False:
        pass
    return result or '0'