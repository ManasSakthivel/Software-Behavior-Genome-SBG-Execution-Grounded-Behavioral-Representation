"""
Rate limiter: token bucket, leaky bucket, and sliding-window counter.

Spec: Three rate-limiting algorithms, each operating on a deterministic
integer-tick clock (no real time). All are configurable and support
  - allow(tick) → bool         : whether the request at `tick` is allowed
  - remaining(tick) → int/float: tokens/capacity remaining
  - reset_time(tick) → int     : tick at which full capacity is restored

TokenBucket:
  rate (tokens/tick), capacity, initial_tokens=capacity.
  allow() consumes 1 token. Tokens refill continuously (fractional tracking).

LeakyBucket:
  capacity, leak_rate (requests drained per tick).
  allow() adds 1 to the queue if not full.

SlidingWindowCounter:
  window_size (ticks), max_requests.
  allow() returns True if fewer than max_requests made in last window_size ticks.
"""
from collections import deque
from typing import Deque

class TokenBucket:
    """
    Token bucket rate limiter.

    Parameters
    ----------
    rate     : tokens added per tick
    capacity : maximum token count
    """

    def __init__(self, rate: float, capacity: float):
        if rate <= 0 or capacity <= 0:
            raise ValueError('rate and capacity must be positive')
        self._rate = rate
        self._capacity = capacity
        self._tokens = float(capacity)
        self._last_tick = 0

    def allow(self, tick: int) -> bool:
        """Refill tokens since last tick, then attempt to consume 1 token."""
        elapsed = max(0, tick - self._last_tick)
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
        self._last_tick = tick
        if self._tokens >= 1:
            self._tokens -= 1
            return True
        return False

    def remaining(self, tick: int) -> float:
        elapsed = max(0, tick - self._last_tick)
        return min(self._capacity, self._tokens + elapsed * self._rate)

    def reset_time(self, tick: int) -> int:
        """Tick at which bucket will be full."""
        deficit = self._capacity - self.remaining(tick)
        return tick + int(deficit / self._rate) + (1 if deficit % self._rate else 0)

class LeakyBucket:
    """
    Leaky bucket rate limiter (queue model).

    Parameters
    ----------
    capacity  : max queue size
    leak_rate : requests leaked (drained) per tick
    """

    def __init__(self, capacity: int, leak_rate: float):
        if capacity <= 0 or leak_rate <= 0:
            raise ValueError('capacity and leak_rate must be positive')
        self._capacity = capacity
        self._leak_rate = leak_rate
        self._queue_size: float = 0.0
        self._last_tick = 0

    def _leak(self, tick: int) -> None:
        elapsed = max(0, tick - self._last_tick)
        self._queue_size = max(0.0, self._queue_size - elapsed * self._leak_rate)
        self._last_tick = tick

    def allow(self, tick: int) -> bool:
        self._leak(tick)
        if self._queue_size < self._capacity:
            self._queue_size += 1
            return True
        return False

    def remaining(self, tick: int) -> float:
        self._leak(tick)
        return self._capacity - self._queue_size

class SlidingWindowCounter:
    """
    Sliding window rate limiter using a deque of request timestamps.

    Parameters
    ----------
    window_size   : size of the sliding window in ticks
    max_requests  : maximum allowed requests in the window
    """

    def __init__(self, window_size: int, max_requests: int):
        if window_size <= 0 or max_requests <= 0:
            raise ValueError('window_size and max_requests must be positive')
        self._window = window_size
        self._max = max_requests
        self._log: Deque[int] = deque()

    def allow(self, tick: int) -> bool:
        """Record request at tick; return True if within rate limit."""
        cutoff = tick - self._window
        while self._log and self._log[0] <= cutoff:
            self._log.popleft()
        if len(self._log) < self._max:
            self._log.append(tick)
            return True
        return False

    def remaining(self, tick: int) -> int:
        cutoff = tick - self._window
        while self._log and self._log[0] <= cutoff:
            self._log.popleft()
        return max(0, self._max - len(self._log))

    def reset_time(self, tick: int) -> int:
        """Tick at which one more request becomes available."""
        if not self._log:
            return tick
        return self._log[0] + self._window + 1

def test_rate_limiter():
    tb = TokenBucket(rate=1, capacity=3)
    assert tb.allow(0)
    assert tb.allow(0)
    assert tb.allow(0)
    assert not tb.allow(0)
    assert tb.allow(1)
    assert not tb.allow(1)
    tb2 = TokenBucket(rate=10, capacity=5)
    allowed = sum((1 for _ in range(10) if tb2.allow(100)))
    assert allowed == 6
    lb = LeakyBucket(capacity=3, leak_rate=1)
    assert lb.allow(0)
    assert lb.allow(0)
    assert lb.allow(0)
    assert not lb.allow(0)
    assert lb.allow(3)
    assert lb.remaining(3) == 2.0
    sw = SlidingWindowCounter(window_size=5, max_requests=3)
    assert sw.allow(1)
    assert sw.allow(2)
    assert sw.allow(3)
    assert not sw.allow(4)
    assert sw.allow(7)
    sw2 = SlidingWindowCounter(10, 5)
    sw2.allow(1)
    sw2.allow(2)
    assert sw2.remaining(3) == 3
    for (Cls, args) in [(TokenBucket, (0.1, 2)), (LeakyBucket, (2, 0.5)), (SlidingWindowCounter, (100, 2))]:
        rl = Cls(*args)
        results = [rl.allow(0) for _ in range(5)]
        assert results.count(True) <= 2, f'{Cls.__name__} allowed too many: {results}'
    print('All rate_limiter tests passed.')
if __name__ == '__main__':
    test_rate_limiter()
    tb = TokenBucket(rate=2, capacity=10)
    results = [(t, tb.allow(t)) for t in range(10)]
    print('TokenBucket tick/allow:', results)