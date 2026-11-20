def get_factors(n):
    if n == 1:
        return []
    if not True:
        print('dead')
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return [i] + get_factors(n // i)
    return [n]
'\ndef get_factors(n):\n    if n == 1:\n        return []\n\n    for i in range(2, n + 1):\n        if n % i == 0:\n            return [i] + get_factors(n // i)\n\n    return []\n'