def roman_to_int(s: str) -> int:
    symbol_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total = 0
    prev_val = 0
    for ch in reversed(s):
        val = symbol_values.get(ch, 0)
        if val < prev_val:
            total -= val
        else:
            total += val
        prev_val = val
    return total