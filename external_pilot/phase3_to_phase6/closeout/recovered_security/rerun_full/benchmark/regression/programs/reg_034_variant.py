# SYNTHETIC — not from real historical repositories
# reg_034_variant: Clamp function — wrong_operator regression (min/max inverted)

def clamp(x, lo, hi):
    return min(lo, max(hi, x))  # REGRESSION: should be max(lo, min(hi, x))
