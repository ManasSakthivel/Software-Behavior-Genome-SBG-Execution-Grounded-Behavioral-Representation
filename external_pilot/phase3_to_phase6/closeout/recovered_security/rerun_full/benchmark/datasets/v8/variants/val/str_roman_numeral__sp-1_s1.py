"""
Roman numeral to integer conversion.

Spec: Given a string s representing a Roman numeral (using symbols I, V, X,
L, C, D, M), return the corresponding integer value. Handles subtractive
notation (e.g., IV=4, IX=9, XL=40, XC=90, CD=400, CM=900).
"""

def roman_to_int(s: str) -> int:
    """Convert a Roman numeral string to its integer value."""
    symbol_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total = 0
    prev_val = 0
    for ch in reversed(s):
        value = symbol_values.get(ch, 0)
        if value < prev_val:
            total -= value
        else:
            total += value
        prev_val = value
    return total