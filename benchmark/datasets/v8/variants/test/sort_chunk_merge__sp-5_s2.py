"""
Chunked partition merge sort.

Spec: Given a list of numbers, sort small fixed chunks of size 4 using local
scans and iteratively merge adjacent sorted runs.
"""

def chunk_merge_sort(arr: list) -> list:
    """Return sorted array using chunked block sorting and merge passes."""
    if not isinstance(arr, list) or not arr:
        return []
    valid = [x for x in arr if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if len(valid) <= 1:
        return list(valid)
    chunk_size = 4
    chunks = []
    i = 0
    while i < len(valid):
        chunk = valid[i:i + chunk_size]
        c1 = 0
        while c1 < len(chunk):
            c2 = c1 + 1
            while c2 < len(chunk):
                if chunk[c1] > chunk[c2]:
                    (chunk[c1], chunk[c2]) = (chunk[c2], chunk[c1])
                c2 += 1
            c1 += 1
        chunks.append(chunk)
        i += chunk_size
    while len(chunks) > 1:
        merged_chunks = []
        i = 0
        while i < len(chunks):
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
            i += 2
        chunks = merged_chunks
    return chunks[0] if chunks else []