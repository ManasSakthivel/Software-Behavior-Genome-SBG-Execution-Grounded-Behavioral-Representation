# SYNTHETIC — not from real historical repositories
# reg_002_variant: Inclusive range sum — off_by_one regression (hi excluded)

def range_sum(lo, hi):
    total = 0
    for i in range(lo, hi):  # REGRESSION: should be range(lo, hi + 1)
        total += i
    return total
