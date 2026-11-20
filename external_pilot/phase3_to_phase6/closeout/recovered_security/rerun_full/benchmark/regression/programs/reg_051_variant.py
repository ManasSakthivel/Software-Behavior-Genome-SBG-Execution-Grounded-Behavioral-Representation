# SYNTHETIC — not from real historical repositories
# reg_051_variant: Exponential backoff — wrong_operator regression (additive instead of multiplicative)

def backoff_delay(base_delay, attempt, cap=60.0):
    delay = base_delay + (2 ** attempt)  # REGRESSION: should be base_delay * (2 ** attempt)
    return min(delay, cap)
