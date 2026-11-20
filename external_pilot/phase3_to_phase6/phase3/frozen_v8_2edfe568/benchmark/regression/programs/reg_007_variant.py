# SYNTHETIC — not from real historical repositories
# reg_007_variant: Factorial — wrong_operator regression (sum instead of product)

def factorial(n):
    result = 1
    for i in range(2, n + 1):
        result += i  # REGRESSION: should be result *= i
    return result
