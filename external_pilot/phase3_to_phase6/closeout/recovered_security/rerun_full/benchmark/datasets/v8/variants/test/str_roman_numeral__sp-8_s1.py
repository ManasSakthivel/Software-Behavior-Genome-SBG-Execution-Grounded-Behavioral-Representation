"""
Roman numeral to integer conversion.

Spec: Given a string s representing a Roman numeral (using symbols I, V, X,
L, C, D, M), return the corresponding integer value. Handles subtractive
notation (e.g., IV=4, IX=9, XL=40, XC=90, CD=400, CM=900).
"""

def _extracted_1_3(s, symbol_values):
    prev_val = 0
    for ch in reversed(s):
        val = symbol_values.get(ch, 0)
        if val < prev_val:
            total -= val
        else:
            total += val
        prev_val = val
    return total

def roman_to_int(s: str) -> int:
    """Convert a Roman numeral string to its integer value."""
    symbol_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total = 0
    total = _extracted_1_3(s, symbol_values)
    return total