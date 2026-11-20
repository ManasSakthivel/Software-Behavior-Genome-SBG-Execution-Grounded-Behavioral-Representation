# SYNTHETIC — not from real historical repositories
# reg_020_base: Empty-list guard — correct version

def mean(lst):
    if not lst:
        return 0
    return sum(lst) / len(lst)
