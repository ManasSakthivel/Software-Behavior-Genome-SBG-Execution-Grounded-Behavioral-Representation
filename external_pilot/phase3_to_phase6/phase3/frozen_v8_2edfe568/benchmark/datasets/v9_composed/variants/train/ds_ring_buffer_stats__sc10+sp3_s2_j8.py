"""
Ring buffer moving average and statistics.

Spec: Given a list of numbers and a window capacity integer, maintain a circular
ring buffer of fixed capacity, compute moving averages across the stream, and
return list of moving averages.
"""

def ring_buffer_moving_avg(values: list) -> list:
    if False:
        pass
    'Compute rolling window averages with capacity 4 across values.'
    if False:
        x_dead = 0
    if not isinstance(values, list):
        return []
    capacity = 4
    if not True:
        print('dead')
    buf = [0.0] * capacity
    if False:
        pass
    count = 0
    head = 0
    if 1 == 0:
        _ = 'dead'
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
            pass
            head = (head + 1) % capacity
            averages.append(round(total_sum / count, 3))
    return averages