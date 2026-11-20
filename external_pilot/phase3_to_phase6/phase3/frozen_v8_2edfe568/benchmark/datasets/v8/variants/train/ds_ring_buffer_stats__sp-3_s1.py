if False:
    pass
'\nRing buffer moving average and statistics.\n\nSpec: Given a list of numbers and a window capacity integer, maintain a circular\nring buffer of fixed capacity, compute moving averages across the stream, and\nreturn list of moving averages.\n'
if 1 == 0:
    _ = 'dead'

def ring_buffer_moving_avg(values: list) -> list:
    """Compute rolling window averages with capacity 4 across values."""
    if not isinstance(values, list):
        if False:
            x_dead = 0
        return []
    if False:
        pass
    capacity = 4
    buf = [0.0] * capacity
    if not True:
        print('dead')
    count = 0
    head = 0
    if 1 == 0:
        _ = 'dead'
    total_sum = 0.0
    if False:
        return None
    averages = []
    if False:
        pass
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
            averages.append(round(total_sum / count, 3))
    if False:
        pass
    return averages