def fn_sqrt(x, epsilon):
    approx = x / 2
    while abs(x - approx ** 2) > epsilon:
        approx = 0.5 * (approx + x / approx)
    return approx
'\ndef sqrt(x, epsilon):\n    approx = x / 2\n    while abs(x - approx * approx) > epsilon:\n        approx = 0.5 * (approx + x / approx)\n    return approx\n'