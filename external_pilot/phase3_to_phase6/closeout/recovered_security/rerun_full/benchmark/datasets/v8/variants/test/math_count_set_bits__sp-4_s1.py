def count_bits_upto(n: int) -> list:
    if not isinstance(n, int) or n < 0:
        return []
    result = []
    for i in range(n + 1):
        x = i
        cnt = 0
        while x > 0:
            x = x & x - 1
            cnt += 1
        result.append(cnt)
    return result