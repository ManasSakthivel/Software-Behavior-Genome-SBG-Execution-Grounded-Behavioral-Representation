# SYNTHETIC — not from real historical repositories
# reg_055_variant: Celsius to Fahrenheit — wrong_constant regression (23 instead of 32)

def celsius_to_fahrenheit(c):
    return (c * 9 / 5) + 23  # REGRESSION: should be + 32
