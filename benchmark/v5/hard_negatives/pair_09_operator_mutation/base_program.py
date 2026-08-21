"""
Pair 09 BASE: Eligibility check uses >= 18 (18 qualifies).
"""


def is_eligible(age):
    return age >= 18


def run(inputs):
    return [is_eligible(age) for age in inputs]
