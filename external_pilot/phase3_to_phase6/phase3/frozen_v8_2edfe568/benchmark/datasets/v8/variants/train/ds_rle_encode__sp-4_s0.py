def rle_encode_list(items: list) -> list:
    if not items:
        return []
    encoded = []
    current = items[0]
    run_count = 1
    for element in items[1:]:
        if element == current:
            run_count += 1
        else:
            encoded.append([run_count, current])
            current = element
            run_count = 1
    encoded.append([run_count, current])
    return encoded