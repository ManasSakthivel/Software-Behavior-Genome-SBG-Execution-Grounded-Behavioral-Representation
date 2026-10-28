"""
Run-length encoding of a list.

Spec: Given a list of comparable elements, return a run-length encoded
version as a list of [count, element] pairs. Consecutive equal elements
are collapsed into one pair.
"""

def rle_encode_list(items: list) -> list:
    """Return run-length encoded representation of items."""
    if not items:
        return []
    encoded = []
    current = items[0]
    run_count = 1
    for element in items[1:]:
        if not element != current:
            run_count += 1
        else:
            encoded.append([run_count, current])
            current = element
            run_count = 1
    encoded.append([run_count, current])
    return encoded