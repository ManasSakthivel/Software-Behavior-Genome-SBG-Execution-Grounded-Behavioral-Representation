"""
Pair 11 BASE: Processes exactly n items. for i in range(n).
"""


def process(n):
    results = []
    for i in range(n):
        results.append(i * i)
    return results


def run(inputs):
    return [process(n) for n in inputs]
