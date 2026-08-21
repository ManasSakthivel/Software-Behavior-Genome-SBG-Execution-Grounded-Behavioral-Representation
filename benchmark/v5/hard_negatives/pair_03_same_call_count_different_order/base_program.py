"""
Pair 03 BASE: Calls validate(), then process(), then finalize() in order.
"""


def validate(data):
    return [x for x in data if x is not None]


def process(data):
    return [x * 2 for x in data]


def finalize(data):
    return sorted(data)


def compute(data):
    validated = validate(data)
    processed = process(validated)
    return finalize(processed)


def run(inputs):
    return [compute(items) for items in inputs]
