"""
Pair 05 BASE: One monolithic function that sorts, filters, and reduces a list.
"""


def process_data(data):
    # Step 1: filter out negatives
    filtered = []
    for x in data:
        if x >= 0:
            filtered.append(x)

    # Step 2: square each element
    squared = []
    for x in filtered:
        squared.append(x * x)

    # Step 3: sort ascending
    n = len(squared)
    for i in range(n):
        for j in range(i + 1, n):
            if squared[i] > squared[j]:
                squared[i], squared[j] = squared[j], squared[i]

    # Step 4: sum the top half
    mid = len(squared) // 2
    total = 0
    for x in squared[mid:]:
        total += x

    return total


def run(inputs):
    return [process_data(lst) for lst in inputs]
