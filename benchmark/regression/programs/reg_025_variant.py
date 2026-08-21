# SYNTHETIC — not from real historical repositories
# reg_025_variant: Label classifier — missing_condition regression (else branch removed)

def classify_score(score):
    if score >= 90:
        label = "A"
    elif score >= 80:
        label = "B"
    elif score >= 70:
        label = "C"
    # REGRESSION: else branch `label = "F"` removed — returns None for score < 70
    return label
