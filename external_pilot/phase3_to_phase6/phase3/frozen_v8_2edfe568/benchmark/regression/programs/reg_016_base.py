# SYNTHETIC — not from real historical repositories
# reg_016_base: Retry logic — correct version

def retry(fn, max_retries=3):
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception:
            if attempt == max_retries:
                raise
