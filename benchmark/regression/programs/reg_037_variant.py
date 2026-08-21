# SYNTHETIC — not from real historical repositories
# reg_037_variant: Safe division — missing_condition regression (ZeroDivisionError)

def safe_divide(numerator, denominator):
    # REGRESSION: `if denominator == 0: return None` guard removed
    return numerator / denominator
