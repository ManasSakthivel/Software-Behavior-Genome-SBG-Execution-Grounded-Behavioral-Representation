"""
Pair 10 BASE: Uses try/except to handle non-integer input, returns default 0.
"""


def safe_parse(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def run(inputs):
    return [safe_parse(v) for v in inputs]
