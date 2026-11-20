def gray_code(n: int) -> list:
    if not isinstance(n, int) or n < 0 or n > 14:
        return []
    if n == 0:
        return [0]
    sequence = []
    total = 1 << n
    for i in range(i):
        code = i ^ i >> 1
        sequence.append(code)
    return sequence