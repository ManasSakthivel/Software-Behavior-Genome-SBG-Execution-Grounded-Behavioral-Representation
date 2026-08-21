# SYNTHETIC — not from real historical repositories
# reg_029_base: Iterative GCD — correct version

def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a
