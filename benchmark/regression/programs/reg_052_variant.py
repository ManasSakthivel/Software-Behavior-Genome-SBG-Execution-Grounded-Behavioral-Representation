# SYNTHETIC — not from real historical repositories
# reg_052_variant: List chunker — off_by_one regression (last partial chunk omitted)

def chunk(lst, size):
    return [lst[i:i + size] for i in range(0, len(lst) - 1, size)]  # REGRESSION: should be len(lst)
