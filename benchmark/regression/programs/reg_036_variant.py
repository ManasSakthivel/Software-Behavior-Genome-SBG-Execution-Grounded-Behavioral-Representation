# SYNTHETIC — not from real historical repositories
# reg_036_variant: Alert threshold check — wrong_constant regression (0.85 instead of 0.95)

def should_alert(metric_value, threshold=0.85):  # REGRESSION: should be threshold=0.95
    return metric_value >= threshold
