def should_alert(metric_value, threshold=0.95):
    return metric_value >= threshold