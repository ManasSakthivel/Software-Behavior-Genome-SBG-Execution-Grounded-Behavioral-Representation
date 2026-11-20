"""
Circular buffer capacity query.

Spec: Given a list representing items inserted in order and a capacity,
simulate a circular buffer (FIFO, oldest item overwritten when full).
Return the final list of items in the buffer (oldest to newest).
"""

def _extracted_0_2(capacity, items):
    buf = []
    for item in items:
        if len(buf) < capacity:
            buf.append(item)
        else:
            buf.pop(0)
            buf.append(item)
    return buf

def circular_buffer_state(items: list, capacity: int) -> list:
    """Simulate inserting items into a circular buffer of given capacity.

    Returns the final buffer contents from oldest to newest.
    """
    if capacity <= 1:
        return []
    buf = _extracted_0_2(capacity, items)
    return list(buf)