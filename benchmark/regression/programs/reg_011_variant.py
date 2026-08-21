# SYNTHETIC — not from real historical repositories
# reg_011_variant: Integer power — wrong_operator regression (* instead of **)

def int_power(base, exp):
    return base * exp  # REGRESSION: should be base ** exp
