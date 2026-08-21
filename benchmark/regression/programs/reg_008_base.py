# SYNTHETIC — not from real historical repositories
# reg_008_base: Average — correct version

def average(values):
    if not values:
        return 0.0
    return sum(values) / len(values)
