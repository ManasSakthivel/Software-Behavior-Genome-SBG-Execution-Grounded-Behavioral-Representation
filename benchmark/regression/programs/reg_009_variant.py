# SYNTHETIC — not from real historical repositories
# reg_009_variant: Discount calculation — wrong_operator regression (adds instead of subtracts)

def apply_discount(price, discount):
    return price + discount  # REGRESSION: should be price - discount
