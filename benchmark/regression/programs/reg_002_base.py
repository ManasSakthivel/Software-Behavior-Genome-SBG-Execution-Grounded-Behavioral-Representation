# SYNTHETIC — not from real historical repositories
# reg_002_base: Inclusive range sum — correct version

def range_sum(lo, hi):
    total = 0
    for i in range(lo, hi + 1):
        total += i
    return total
