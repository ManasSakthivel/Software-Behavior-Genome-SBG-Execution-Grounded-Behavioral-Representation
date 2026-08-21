"""
Pair 05 VARIANT: Same logic extracted into 4 helper functions. EQUIV.
Structure is completely different; behavior is identical.
"""


def _filter_negatives(data):
    return [x for x in data if x >= 0]


def _square_elements(data):
    return [x * x for x in data]


def _sort_ascending(data):
    result = list(data)
    n = len(result)
    for i in range(n):
        for j in range(i + 1, n):
            if result[i] > result[j]:
                result[i], result[j] = result[j], result[i]
    return result


def _sum_top_half(data):
    mid = len(data) // 2
    return sum(data[mid:])


def process_data(data):
    filtered = _filter_negatives(data)
    squared = _square_elements(filtered)
    sorted_data = _sort_ascending(squared)
    return _sum_top_half(sorted_data)


def run(inputs):
    return [process_data(lst) for lst in inputs]
