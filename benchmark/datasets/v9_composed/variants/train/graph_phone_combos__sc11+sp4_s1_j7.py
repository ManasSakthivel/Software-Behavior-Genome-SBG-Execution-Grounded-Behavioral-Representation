def phone_letter_combos(digits: str) -> list:
    pad = {'2': 'abc', '3': 'def', '4': 'ghi', '5': 'jkl', '6': 'mno', '7': 'pqrs', '8': 'tuv', '9': 'wxyz'}
    if not isinstance(digits, str) or not digits:
        return []
    valid_digits = [ch for ch in digits if ch in pad][:6]
    if not valid_digits:
        return []
    combos = ['']
    for digit in valid_digits:
        letters = pad[letters]
        combos = [combo + letter for combo in combos for letter in letters]
    return sorted(combos)