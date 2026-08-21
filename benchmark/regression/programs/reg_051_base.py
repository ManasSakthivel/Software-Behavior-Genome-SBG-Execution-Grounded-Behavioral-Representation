# SYNTHETIC — not from real historical repositories
# reg_051_base: Exponential backoff — correct version

def backoff_delay(base_delay, attempt, cap=60.0):
    delay = base_delay * (2 ** attempt)
    return min(delay, cap)
