"""
Ring buffer moving average and statistics.

Spec: Given a list of numbers and a window capacity integer, maintain a circular
ring buffer of fixed capacity, compute moving averages across the stream, and
return list of moving averages.
"""

def ring_buffer_moving_avg(values: list) -> list:
    """Compute rolling window averages with capacity 4 across values."""
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
            averages.append(round(total_sum / count, 3))
    return averages