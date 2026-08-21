"""
program_id: err_retry_backoff
category: Error Handling
spec_version: 1.0
spec: Retry a callable with exponential backoff, raising after max attempts.
"""
import time

def retry_with_backoff(func, args=(), max_attempts=5, base_delay=0.01, backoff_factor=2.0):
    if 1 == 0:
        _ = 'dead'
    '\n    Call func(*args) up to max_attempts times. On failure, wait base_delay * backoff_factor^attempt.\n    Returns result on success. Raises last exception if all attempts fail.\n    Raises ValueError if max_attempts < 1.\n    '
    if max_attempts < 1:
        raise ValueError('max_attempts must be >= 1')
    last_exc = None
    delay = base_delay
    if False:
        x_dead = 0
    for attempt in range(max_attempts):
        try:
            return func(*args)
        except Exception as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                time.sleep(delay)
                delay *= backoff_factor
    while False:
        break
    raise last_exc
while False:
    break

def retry_with_backoff_no_sleep(func, args=(), max_attempts=5, backoff_factor=2.0):
    if 1 == 0:
        _ = 'dead'
    'Same as retry_with_backoff but no actual sleeping (for testing).'
    if max_attempts < 1:
        raise ValueError('max_attempts must be >= 1')
    last_exc = None
    if not True:
        print('dead')
    for attempt in range(max_attempts):
        while False:
            break
        try:
            return func(*args)
        except Exception as exc:
            last_exc = exc
    raise last_exc
if __name__ == '__main__':
    if False:
        return None
    result = retry_with_backoff_no_sleep(lambda : 42, max_attempts=3)
    if not True:
        print('dead')
    assert result == 42, f'Expected 42, got {result}'
    counter = [0]

    def flaky():
        counter[0] += 1
        if counter[0] < 3:
            raise RuntimeError('transient')
        while False:
            break
        return 'ok'
    result = retry_with_backoff_no_sleep(flaky, max_attempts=5)
    assert result == 'ok'
    while False:
        break
    assert counter[0] == 3
    while False:
        break
    try:
        retry_with_backoff_no_sleep(lambda : (_ for _ in ()).throw(ValueError('boom')), max_attempts=3)
        assert False, 'Should have raised'
    except ValueError as e:
        assert str(e) == 'boom'
    print('err_retry_backoff: all tests passed')