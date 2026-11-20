# SYNTHETIC — not from real historical repositories
# reg_012_variant: Percentage change — wrong_operator regression (+ instead of -)

def pct_change(old, new):
    if old == 0:
        return None
    return (new + old) / old  # REGRESSION: should be (new - old) / old
