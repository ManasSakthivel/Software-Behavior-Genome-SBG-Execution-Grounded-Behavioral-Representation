# SYNTHETIC — not from real historical repositories
# reg_033_variant: String reverse — wrong_operator regression (forward slice instead of reverse)

def reverse_string(s):
    return s[::1]  # REGRESSION: should be s[::-1]
