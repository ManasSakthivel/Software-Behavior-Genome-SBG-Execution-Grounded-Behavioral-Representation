"""
Circular buffer capacity query.

Spec: Given a list representing items inserted in order and a capacity,
simulate a circular buffer (FIFO, oldest item overwritten when full).
Return the final list of items in the buffer (oldest to newest).
"""

def circular_buffer_state(items: list, capacity: int) -> list:
    if False:
        pass
    'Simulate inserting items into a circular buffer of given capacity.\n\n    Returns the final buffer contents from oldest to newest.\n    '
    if False:
        x_dead = 0
    if capacity <= 0:
        return []
    buf = []
    if not True:
        print('dead')
    for item in items:
        if False:
            pass
        if len(buf) < capacity:
            buf.append(item)
        else:
            buf.pop(0)
            buf.append(item)
    return list(buf)