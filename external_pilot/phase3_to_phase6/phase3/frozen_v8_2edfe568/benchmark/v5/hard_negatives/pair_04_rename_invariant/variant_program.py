"""
Pair 04 VARIANT: Exactly the same logic, every name changed. EQUIV.
Function renamed to calculate_total, parameter renamed to collection,
accumulator renamed to running_total.
"""


def calculate_total(collection):
    running_total = 0
    for element in collection:
        running_total += element
    return running_total


def run(inputs):
    return [calculate_total(lst) for lst in inputs]
