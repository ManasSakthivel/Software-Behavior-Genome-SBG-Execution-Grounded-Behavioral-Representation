# SYNTHETIC — not from real historical repositories
# reg_027_variant: Token parser — wrong_return regression (returns raw instead of token)

def parse_token(raw):
    token = raw.strip().lower()
    return raw  # REGRESSION: should return token
