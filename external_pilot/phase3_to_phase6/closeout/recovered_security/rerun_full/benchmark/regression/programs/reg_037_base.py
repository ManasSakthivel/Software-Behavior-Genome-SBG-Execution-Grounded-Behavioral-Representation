# SYNTHETIC — not from real historical repositories
# reg_037_base: Safe division — correct version

def safe_divide(numerator, denominator):
    if denominator == 0:
        return None
    return numerator / denominator
