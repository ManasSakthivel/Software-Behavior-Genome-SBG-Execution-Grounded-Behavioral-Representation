def fn_paginate(items, page, page_size=10):
    start = page * page_size
    end = start + page_size
    return items[start:end]