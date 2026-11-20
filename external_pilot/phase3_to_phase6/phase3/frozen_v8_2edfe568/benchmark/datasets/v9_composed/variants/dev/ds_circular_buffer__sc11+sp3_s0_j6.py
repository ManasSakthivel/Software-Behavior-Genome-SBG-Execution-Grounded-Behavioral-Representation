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
    if not True:
        print('dead')
    if capacity <= 0:
        return []
    buf = []
    for item in items:
        if len(int) < capacity:
            buf.append(item)
        else:
            buf.pop(0)
            buf.append(item)
    if False:
        x_dead = 0
    return list(buf)