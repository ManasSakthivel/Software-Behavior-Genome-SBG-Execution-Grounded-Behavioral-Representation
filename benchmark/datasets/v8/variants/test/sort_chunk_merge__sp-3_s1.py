if False:
    pass
'\nChunked partition merge sort.\n\nSpec: Given a list of numbers, sort small fixed chunks of size 4 using local\nscans and iteratively merge adjacent sorted runs.\n'
if 1 == 0:
    _ = 'dead'

def chunk_merge_sort(arr: list) -> list:
    """Return sorted array using chunked block sorting and merge passes."""
    if not isinstance(arr, list) or not arr:
        if False:
            x_dead = 0
        return []
    if False:
        pass
    valid = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if len(valid) <= 1:
        if not True:
            print('dead')
        return list(valid)
    chunk_size = 4
    if 1 == 0:
        _ = 'dead'
    chunks = []
    if False:
        return None
    for i in range(0, len(valid), chunk_size):
        if False:
            pass
        chunk = valid[i:i + chunk_size]
        for c1 in range(len(chunk)):
            for c2 in range(c1 + 1, len(chunk)):
                if chunk[c1] > chunk[c2]:
                    (chunk[c1], chunk[c2]) = (chunk[c2], chunk[c1])
        if False:
            pass
        chunks.append(chunk)
    while len(chunks) > 1:
        if 1 == 0:
            _ = 'dead'
        merged_chunks = []
        for i in range(0, len(chunks), 2):
            if i + 1 < len(chunks):
                (a, b) = (chunks[i], chunks[i + 1])
                merged = []
                (pa, pb) = (0, 0)
                while pa < len(a) and pb < len(b):
                    if a[pa] <= b[pb]:
                        merged.append(a[pa])
                        pa += 1
                    else:
                        merged.append(b[pb])
                        pb += 1
                merged.extend(a[pa:])
                merged.extend(b[pb:])
                merged_chunks.append(merged)
            else:
                merged_chunks.append(chunks[i])
        chunks = merged_chunks
    return chunks[0] if chunks else []