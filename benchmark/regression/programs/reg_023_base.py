# SYNTHETIC — not from real historical repositories
# reg_023_base: Stack push with overflow guard — correct version

class BoundedStack:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = []

    def push(self, item):
        if len(self.data) >= self.capacity:
            raise OverflowError("stack is full")
        self.data.append(item)

    def pop(self):
        if not self.data:
            raise IndexError("stack is empty")
        return self.data.pop()

    @property
    def size(self):
        return len(self.data)
