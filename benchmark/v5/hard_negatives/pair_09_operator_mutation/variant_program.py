"""
Pair 09 VARIANT: Eligibility check uses > 18 (18 does NOT qualify). CHANGED.
Single operator change: >= → >. Boundary case age=18 diverges.
"""


def is_eligible(age):
    return age > 18  # CHANGED: >= → >


def run(inputs):
    return [is_eligible(age) for age in inputs]
