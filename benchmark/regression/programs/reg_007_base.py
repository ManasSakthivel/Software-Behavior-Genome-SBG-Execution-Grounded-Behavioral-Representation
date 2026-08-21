# SYNTHETIC — not from real historical repositories
# reg_007_base: Factorial — correct version

def factorial(n):
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
