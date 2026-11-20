# SYNTHETIC — not from real historical repositories
# reg_029_variant: Iterative GCD — wrong_return regression (returns b which is always 0)

def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return b  # REGRESSION: should return a (b is 0 at loop exit)
