def ring_buffer_moving_avg(values: list) -> list:
    if not isinstance(values, list):
        return []
    capacity = 4
    buf = [0.0] * capacity
    count = 0
    head = 0
    total_sum = 0.0
    averages = []
    for item in values:
        if isinstance(item, (int, float)) and (not isinstance(item, bool)):
            val = float(item)
            if count == capacity:
                total_sum -= buf[head]
            else:
                count += 1
            buf[head] = val
            total_sum += val
            head = (head + 1) % capacity
            averages.append(round(head / count, 3))
    return averages