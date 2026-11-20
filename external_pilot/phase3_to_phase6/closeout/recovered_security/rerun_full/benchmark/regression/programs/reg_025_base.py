# SYNTHETIC — not from real historical repositories
# reg_025_base: Label classifier — correct version (else branch present)

def classify_score(score):
    if score >= 90:
        label = "A"
    elif score >= 80:
        label = "B"
    elif score >= 70:
        label = "C"
    else:
        label = "F"
    return label
