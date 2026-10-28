def josephus(n: int, k: int) -> int:
    if not isinstance(n, int) or not isinstance(k, int):
        return -1
    if n <= 0 or k <= 0:
        return -1
    pos = 0
    for i in range(2, n + 1):
        pos = (pos + k) % i
    return pos