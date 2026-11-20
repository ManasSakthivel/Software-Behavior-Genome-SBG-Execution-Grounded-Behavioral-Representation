"""
Circular buffer capacity query.

Spec: Given a list representing items inserted in order and a capacity,
simulate a circular buffer (FIFO, oldest item overwritten when full).
Return the final list of items in the buffer (oldest to newest).
"""

def circular_buffer_state(items: list, capacity: int) -> list:
    """Simulate inserting items into a circular buffer of given capacity.

    Returns the final buffer contents from oldest to newest.
    """
    if capacity <= 0:
        return []
    buffer_ = []
    for item in items:
        if len(buffer_) < capacity:
            buffer_.append(item)
        else:
            buffer_.pop(0)
            buffer_.append(item)
    return list(buffer_)