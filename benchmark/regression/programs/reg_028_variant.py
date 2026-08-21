# SYNTHETIC — not from real historical repositories
# reg_028_variant: Sort key extractor — wrong_return regression (sorts by id instead of priority)

def sort_by_priority(items):
    return sorted(items, key=lambda item: item['id'])  # REGRESSION: should be item['priority']
