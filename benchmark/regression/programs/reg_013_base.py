# SYNTHETIC — not from real historical repositories
# reg_013_base: Rate limiter — correct version

class RateLimiter:
    def __init__(self, max_requests=100):
        self.max_requests = max_requests
        self.count = 0

    def allow(self):
        if self.count >= self.max_requests:
            return False
        self.count += 1
        return True

    def reset(self):
        self.count = 0
