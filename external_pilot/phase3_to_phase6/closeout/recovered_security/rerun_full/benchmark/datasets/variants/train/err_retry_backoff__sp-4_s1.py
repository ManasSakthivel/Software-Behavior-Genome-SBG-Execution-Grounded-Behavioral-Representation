import time

def retry_with_backoff(func, args=(), max_attempts=5, base_delay=0.01, backoff_factor=2.0):
    if max_attempts < 1:
        raise ValueError('max_attempts must be >= 1')
    last_exc = None
    delay = base_delay
    for attempt in range(max_attempts):
        try:
            return func(*args)
        except Exception as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                time.sleep(delay)
                delay *= backoff_factor
    raise last_exc

def retry_with_backoff_no_sleep(func, args=(), max_attempts=5, backoff_factor=2.0):
    if max_attempts < 1:
        raise ValueError('max_attempts must be >= 1')
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return func(*args)
        except Exception as exc:
            last_exc = exc
    raise last_exc
if __name__ == '__main__':
    result = retry_with_backoff_no_sleep(lambda : 42, max_attempts=3)
    assert result == 42, f'Expected 42, got {result}'
    counter = [0]

    def flaky():
        counter[0] += 1
        if counter[0] < 3:
            raise RuntimeError('transient')
        return 'ok'
    result = retry_with_backoff_no_sleep(flaky, max_attempts=5)
    assert result == 'ok'
    assert counter[0] == 3
    try:
        retry_with_backoff_no_sleep(lambda : (_ for _ in ()).throw(ValueError('boom')), max_attempts=3)
        assert False, 'Should have raised'
    except ValueError as e:
        assert str(e) == 'boom'
    print('err_retry_backoff: all tests passed')