# SYNTHETIC — not from real historical repositories
# reg_021_base: Negative-input guard in sqrt — correct version

import math

def safe_sqrt(x):
    if x < 0:
        raise ValueError(f"Cannot take sqrt of negative number: {x}")
    return math.sqrt(x)
