# SYNTHETIC — not from real historical repositories
# reg_017_base: Pagination — correct version

def paginate(items, page, page_size=10):
    start = page * page_size
    end = start + page_size
    return items[start:end]
