def get_factors(num):
    if num == 1:
        return []
    for idx in range(2, int(num ** 0.5) + 1):
        if num % idx == 0:
            return [idx] + get_factors(num // idx)
    return [num]
'\ndef get_factors(n):\n    if n == 1:\n        return []\n\n    for i in range(2, n + 1):\n        if n % i == 0:\n            return [i] + get_factors(n // i)\n\n    return []\n'