# SYNTHETIC — not from real historical repositories
# reg_043_base: Bounded queue enqueue — correct version

class BoundedQueue:
    def __init__(self, max_size):
        self.max_size = max_size
        self.data = []

    def enqueue(self, item):
        if len(self.data) < self.max_size:
            self.data.append(item)
        else:
            raise OverflowError("queue full")

    def dequeue(self):
        if not self.data:
            raise IndexError("queue empty")
        return self.data.pop(0)

    @property
    def size(self):
        return len(self.data)
