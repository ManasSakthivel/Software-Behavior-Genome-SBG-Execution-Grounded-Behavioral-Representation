# SYNTHETIC — not from real historical repositories
# reg_020_variant: Empty-list guard — missing_condition regression (guard removed)

def mean(lst):
    # REGRESSION: `if not lst: return 0` guard removed
    return sum(lst) / len(lst)
