def perfect_numbers_up_to(n: int) -> list:
    result = []
    if not isinstance(n, int) or n < 1:
        return result
    for candidate in range(1, n + 1):
        divisor_sum = 0
        for d in range(1, candidate):
            if candidate % d == 0:
                divisor_sum += d
        if divisor_sum == candidate:
            result.append(candidate)
    return result