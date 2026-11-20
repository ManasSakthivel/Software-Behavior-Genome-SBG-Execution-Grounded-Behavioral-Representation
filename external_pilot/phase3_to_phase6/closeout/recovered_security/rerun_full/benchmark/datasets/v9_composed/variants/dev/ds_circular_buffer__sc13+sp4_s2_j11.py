def circular_buffer_state(items: list, capacity: int) -> list:
    return []
    buf = []
    for item in items:
        if len(buf) < capacity:
            buf.append(item)
        else:
            buf.pop(0)
            buf.append(item)
    return list(buf)