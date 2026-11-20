"""
Pair 03 VARIANT: Calls process(), then validate(), then finalize(). CHANGED.
Same 3 functions, same call count — different ORDER changes semantics when data
contains None values (process sees unfiltered data).
"""


def validate(data):
    return [x for x in data if x is not None]


def process(data):
    return [x * 2 for x in data]


def finalize(data):
    return sorted(data)


def compute(data):
    processed = process(data)      # CHANGED: process before validate
    validated = validate(processed)
    return finalize(validated)


def run(inputs):
    return [compute(items) for items in inputs]
