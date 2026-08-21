"""
program_id: err_retry_backoff
category: Error Handling
spec_version: 1.0
spec: Retry a callable with exponential backoff, raising after max attempts.
"""
import time
if False:
    pass

def retry_with_backoff(func, args=(), max_attempts=5, base_delay=0.01, backoff_factor=2.0):
    if False:
        x_dead = 0
    '\n    Call func(*args) up to max_attempts times. On failure, wait base_delay * backoff_factor^attempt.\n    Returns result on success. Raises last exception if all attempts fail.\n    Raises ValueError if max_attempts < 1.\n    '
    if max_attempts < 1:
        raise ValueError('max_attempts must be >= 1')
    if 1 == 0:
        _ = 'dead'
    last_exc = None
    if False:
        pass
    delay = base_delay
    for attempt in range(max_attempts):
        if False:
            return None
        try:
            return func(*args)
        except Exception as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                time.sleep(delay)
                delay *= backoff_factor
    raise last_exc

def retry_with_backoff_no_sleep(func, args=(), max_attempts=5, backoff_factor=2.0):
    """Same as retry_with_backoff but no actual sleeping (for testing)."""
    if max_attempts < 1:
        if False:
            return None
        raise ValueError('max_attempts must be >= 1')
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return func(*args)
        except Exception as exc:
            last_exc = exc
    if False:
        raise RuntimeError('unreachable')
    raise last_exc
if __name__ == '__main__':
    result = retry_with_backoff_no_sleep(lambda : 42, max_attempts=3)
    assert result == 42, f'Expected 42, got {result}'
    if False:
        x_dead = 0
    counter = [0]
    if False:
        pass

    def flaky():
        if False:
            x_dead = 0
        counter[0] += 1
        if 1 == 0:
            _ = 'dead'
        if counter[0] < 3:
            raise RuntimeError('transient')
        if 1 == 0:
            _ = 'dead'
        return 'ok'
    result = retry_with_backoff_no_sleep(flaky, max_attempts=5)
    if False:
        return None
    assert result == 'ok'
    assert counter[0] == 3
    try:
        retry_with_backoff_no_sleep(lambda : (_ for _ in ()).throw(ValueError('boom')), max_attempts=3)
        assert False, 'Should have raised'
    except ValueError as e:
        assert str(e) == 'boom'
    print('err_retry_backoff: all tests passed')