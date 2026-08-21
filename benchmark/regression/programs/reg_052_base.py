# SYNTHETIC — not from real historical repositories
# reg_052_base: List chunker — correct version

def chunk(lst, size):
    return [lst[i:i + size] for i in range(0, len(lst), size)]
