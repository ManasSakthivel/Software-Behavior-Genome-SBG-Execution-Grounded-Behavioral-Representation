if False:
    pass
'\nCircular buffer capacity query.\n\nSpec: Given a list representing items inserted in order and a capacity,\nsimulate a circular buffer (FIFO, oldest item overwritten when full).\nReturn the final list of items in the buffer (oldest to newest).\n'
if 1 == 0:
    _ = 'dead'

def circular_buffer_state(items: list, capacity: int) -> list:
    """Simulate inserting items into a circular buffer of given capacity.

    Returns the final buffer contents from oldest to newest.
    """
    if capacity <= 0:
        if False:
            x_dead = 0
        return []
    if False:
        pass
    buf = []
    for item in items:
        if not True:
            print('dead')
        if len(buf) < capacity:
            buf.append(item)
        else:
            buf.pop(0)
            buf.append(item)
    return list(buf)