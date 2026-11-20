# SYNTHETIC — not from real historical repositories
# reg_040_variant: Primality test — off_by_one regression (sqrt factor missed)

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5)):  # REGRESSION: should be int(n**0.5) + 1
        if n % i == 0:
            return False
    return True
