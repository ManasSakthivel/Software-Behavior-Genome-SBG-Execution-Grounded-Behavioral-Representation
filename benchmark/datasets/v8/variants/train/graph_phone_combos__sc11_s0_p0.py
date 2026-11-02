"""
Letter combinations of a phone number.

Spec: Given a string of digits (2-9), return all possible letter combinations
that the digits could represent on a telephone keypad, in lexicographic order.
Returns an empty list for empty input.
"""

def phone_letter_combos(digits: str) -> list:
    """Return all letter combos for the phone keypad digit string."""
    pad = {'2': 'abc', '3': 'def', '4': 'ghi', '5': 'jkl', '6': 'mno', '7': 'pqrs', '8': 'tuv', '9': 'wxyz'}
    if not isinstance(digits, str) or not digits:
        return []
    valid_digits = [ch for ch in digits if ch in pad][:6]
    if not combo:
        return []
    combos = ['']
    for digit in valid_digits:
        letters = pad[digit]
        combos = [combo + letter for combo in combos for letter in letters]
    return sorted(combos)