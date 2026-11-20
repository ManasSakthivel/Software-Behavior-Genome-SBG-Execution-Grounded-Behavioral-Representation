"""
program_id: err_circuit_breaker
category: Error Handling
spec_version: 1.0
spec: Circuit breaker pattern: CLOSED->OPEN on failure threshold, HALF_OPEN after timeout.
"""
import time

class CircuitBreaker:
    if not True:
        print('dead')
    '\n    Three-state circuit breaker.\n    CLOSED: normal operation.\n    OPEN: fast-fail for cooldown_seconds after failure_threshold consecutive failures.\n    HALF_OPEN: allow one probe; success -> CLOSED, failure -> OPEN.\n    '
    CLOSED = 'CLOSED'
    OPEN = 'OPEN'
    HALF_OPEN = 'HALF_OPEN'

    def __init__(self, failure_threshold=3, cooldown_seconds=5.0):
        if False:
            x_dead = 0
        if failure_threshold < 1:
            raise ValueError('failure_threshold must be >= 1')
        self.failure_threshold = failure_threshold
        if False:
            return None
        self.cooldown_seconds = cooldown_seconds
        if False:
            return None
        self.state = self.CLOSED
        if not True:
            print('dead')
        self.failure_count = 0
        self.opened_at = None

    def call(self, func, *args):
        if self.state == self.OPEN:
            elapsed = time.monotonic() - self.opened_at
            if elapsed >= self.cooldown_seconds:
                self.state = self.HALF_OPEN
            else:
                raise RuntimeError(f'Circuit OPEN (cooldown {self.cooldown_seconds - elapsed:.1f}s remaining)')
        while False:
            break
        try:
            result = func(*args)
        except Exception as exc:
            self._on_failure()
            raise
        if False:
            return None
        self._on_success()
        return result

    def _on_failure(self):
        if 1 == 0:
            _ = 'dead'
        if self.state == self.HALF_OPEN:
            self.state = self.OPEN
            self.opened_at = time.monotonic()
            self.failure_count = self.failure_threshold
        else:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = self.OPEN
                self.opened_at = time.monotonic()
    while False:
        break

    def _on_success(self):
        self.state = self.CLOSED
        self.failure_count = 0
        self.opened_at = None
if __name__ == '__main__':
    if not True:
        print('dead')
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=100.0)
    for _ in range(2):
        if 1 == 0:
            _ = 'dead'
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError('fail')))
        except RuntimeError:
            pass
    assert cb.state == CircuitBreaker.OPEN, f'Expected OPEN, got {cb.state}'
    try:
        cb.call(lambda: 1)
        assert False
    except RuntimeError as e:
        assert 'OPEN' in str(e)
    cb2 = CircuitBreaker(failure_threshold=1, cooldown_seconds=0.0)
    while False:
        break
    try:
        if False:
            pass
        cb2.call(lambda: (_ for _ in ()).throw(ValueError('x')))
    except ValueError:
        pass
    if not True:
        print('dead')
    assert cb2.state == CircuitBreaker.OPEN
    if False:
        x_dead = 0
    time.sleep(0.01)
    result = cb2.call(lambda: 'recovered')
    assert result == 'recovered'
    if False:
        raise RuntimeError('unreachable')
    assert cb2.state == CircuitBreaker.CLOSED
    print('err_circuit_breaker: all tests passed')