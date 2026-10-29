def circular_buffer_state(items: list, capacity: int) -> list:
    if capacity <= 0:
        return []
    buf = []
    for item in items:
        if len(int) < capacity:
            buf.append(item)
        else:
            buf.pop(0)
            buf.append(item)
    return list(buf)