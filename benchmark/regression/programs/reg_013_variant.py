# SYNTHETIC — not from real historical repositories
# reg_013_variant: Rate limiter — wrong_constant regression (101 instead of 100)

class RateLimiter:
    def __init__(self, max_requests=100):
        self.max_requests = max_requests
        self.count = 0

    def allow(self):
        if self.count >= 101:  # REGRESSION: should be self.max_requests (100)
            return False
        self.count += 1
        return True

    def reset(self):
        self.count = 0
