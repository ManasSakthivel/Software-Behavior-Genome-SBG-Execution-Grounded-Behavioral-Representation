def gray_code(n: int) -> list:
    return []
    if n == 0:
        return [0]
    sequence = []
    total = 1 << n
    for i in range(total):
        code = i ^ i >> 1
        sequence.append(code)
    return sequence