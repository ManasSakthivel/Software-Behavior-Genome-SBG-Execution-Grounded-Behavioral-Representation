# SYNTHETIC — not from real historical repositories
# reg_008_variant: Average — wrong_operator regression (product instead of quotient)

def average(values):
    if not values:
        return 0.0
    return sum(values) * len(values)  # REGRESSION: should be / len(values)
