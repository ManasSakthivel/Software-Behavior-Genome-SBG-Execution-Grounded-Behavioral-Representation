"""
Pair 10 VARIANT: Uses isinstance guard instead of try/except. EQUIV.
No exception is ever raised — same logical behavior, zero exception fraction.
A detector that sees exception_fraction(base)=high, exception_fraction(variant)=0
might wrongly label this CHANGED.
"""


def safe_parse(value):
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        if value.lstrip("-").isdigit():
            return int(value)
    return 0


def run(inputs):
    return [safe_parse(v) for v in inputs]
