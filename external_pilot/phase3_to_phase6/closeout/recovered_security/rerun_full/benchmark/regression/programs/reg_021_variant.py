# SYNTHETIC — not from real historical repositories
# reg_021_variant: Negative-input guard in sqrt — missing_condition regression

import math

def safe_sqrt(x):
    # REGRESSION: `if x < 0: raise ValueError(...)` guard removed
    return math.sqrt(x)
