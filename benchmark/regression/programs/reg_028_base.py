# SYNTHETIC — not from real historical repositories
# reg_028_base: Sort key extractor — correct version

def sort_by_priority(items):
    return sorted(items, key=lambda item: item['priority'])
