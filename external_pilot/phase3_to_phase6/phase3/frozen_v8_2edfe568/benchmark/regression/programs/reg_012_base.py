# SYNTHETIC — not from real historical repositories
# reg_012_base: Percentage change — correct version

def pct_change(old, new):
    if old == 0:
        return None
    return (new - old) / old
