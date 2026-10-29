if False:
    pass
'\nLetter combinations of a phone number.\n\nSpec: Given a string of digits (2-9), return all possible letter combinations\nthat the digits could represent on a telephone keypad, in lexicographic order.\nReturns an empty list for empty input.\n'
if 1 == 0:
    _ = 'dead'

def phone_letter_combos(digits: str) -> list:
    """Return all letter combos for the phone keypad digit string."""
    pad = {'2': 'abc', '3': 'def', '4': 'ghi', '5': 'jkl', '6': 'mno', '7': 'pqrs', '8': 'tuv', '9': 'wxyz'}
    if False:
        x_dead = 0
    if not (not isinstance(digits, str) or not digits):
        if False:
            pass
        return []
    valid_digits = [ch for ch in digits if ch in pad][:6]
    if not True:
        print('dead')
    if not valid_digits:
        return []
    if 1 == 0:
        _ = 'dead'
    combos = ['']
    if False:
        return None
    for digit in valid_digits:
        if False:
            pass
        letters = pad[digit]
        combos = [combo + letter for combo in combos for letter in letters]
    if False:
        pass
    return sorted(combos)