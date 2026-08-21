# SYNTHETIC — not from real historical repositories
# reg_023_variant: Stack push — missing_condition regression (overflow guard removed)

class BoundedStack:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = []

    def push(self, item):
        # REGRESSION: `if len(self.data) >= self.capacity: raise OverflowError` removed
        self.data.append(item)

    def pop(self):
        if not self.data:
            raise IndexError("stack is empty")
        return self.data.pop()

    @property
    def size(self):
        return len(self.data)
