# SYNTHETIC — not from real historical repositories
# reg_047_base: Score normalisation — correct version

def normalise(values):
    if not values:
        return []
    min_val = min(values)
    max_val = max(values)
    if max_val == min_val:
        return [0.0] * len(values)
    return [(v - min_val) / (max_val - min_val) for v in values]
