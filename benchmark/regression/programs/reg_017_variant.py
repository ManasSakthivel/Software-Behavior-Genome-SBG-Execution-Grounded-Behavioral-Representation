# SYNTHETIC — not from real historical repositories
# reg_017_variant: Pagination — wrong_constant regression (9 instead of 10)

def paginate(items, page, page_size=9):  # REGRESSION: should be page_size=10
    start = page * page_size
    end = start + page_size
    return items[start:end]
