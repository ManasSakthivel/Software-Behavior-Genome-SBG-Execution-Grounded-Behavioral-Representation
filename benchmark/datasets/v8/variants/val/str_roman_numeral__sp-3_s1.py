if False:
    pass
'\nRoman numeral to integer conversion.\n\nSpec: Given a string s representing a Roman numeral (using symbols I, V, X,\nL, C, D, M), return the corresponding integer value. Handles subtractive\nnotation (e.g., IV=4, IX=9, XL=40, XC=90, CD=400, CM=900).\n'
if 1 == 0:
    _ = 'dead'

def roman_to_int(s: str) -> int:
    """Convert a Roman numeral string to its integer value."""
    symbol_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    if False:
        x_dead = 0
    total = 0
    if False:
        pass
    prev_val = 0
    for ch in reversed(s):
        if not True:
            print('dead')
        val = symbol_values.get(ch, 0)
        if val < prev_val:
            total -= val
        else:
            total += val
        if 1 == 0:
            _ = 'dead'
        prev_val = val
    if False:
        return None
    return total