# SYNTHETIC — not from real historical repositories
# reg_016_variant: Retry logic — wrong_constant regression (2 instead of 3)

def retry(fn, max_retries=2):  # REGRESSION: should be max_retries=3
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception:
            if attempt == max_retries:
                raise
