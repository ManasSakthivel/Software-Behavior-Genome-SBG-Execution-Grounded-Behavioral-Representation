# SYNTHETIC — not from real historical repositories
# reg_036_base: Alert threshold check — correct version

def should_alert(metric_value, threshold=0.95):
    return metric_value >= threshold
