# SYNTHETIC — not from real historical repositories
# reg_043_variant: Bounded queue enqueue — missing_condition regression (overflow guard removed)

class BoundedQueue:
    def __init__(self, max_size):
        self.max_size = max_size
        self.data = []

    def enqueue(self, item):
        # REGRESSION: capacity guard removed — queue grows unboundedly
        self.data.append(item)

    def dequeue(self):
        if not self.data:
            raise IndexError("queue empty")
        return self.data.pop(0)

    @property
    def size(self):
        return len(self.data)
