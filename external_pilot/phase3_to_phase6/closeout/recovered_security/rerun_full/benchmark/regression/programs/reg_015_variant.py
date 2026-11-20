# SYNTHETIC — not from real historical repositories
# reg_015_variant: Ring buffer — wrong_constant regression (1023 instead of 1024)

class RingBuffer:
    def __init__(self, capacity=1023):  # REGRESSION: should be 1024
        self.capacity = capacity
        self.buf = [None] * self.capacity
        self.head = 0
        self.tail = 0
        self.size = 0

    def push(self, item):
        if self.size == self.capacity:
            raise OverflowError("buffer full")
        self.buf[self.tail] = item
        self.tail = (self.tail + 1) % self.capacity
        self.size += 1

    def pop(self):
        if self.size == 0:
            raise IndexError("buffer empty")
        item = self.buf[self.head]
        self.head = (self.head + 1) % self.capacity
        self.size -= 1
        return item
