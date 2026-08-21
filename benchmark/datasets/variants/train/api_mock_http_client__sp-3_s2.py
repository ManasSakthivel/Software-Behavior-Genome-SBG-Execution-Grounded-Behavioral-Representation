"""
Mock HTTP client with request/response simulation, retry logic, and middleware.

Spec: Simulates HTTP request/response cycles without making real network calls.
A MockServer holds a routing table (method + path → handler function).
A MockClient sends requests to a MockServer.

Features:
  - Route registration: server.route(method, path, handler)
  - Request dispatch: client.request(method, path, body=None, headers=None)
  - Middleware pipeline: client.use(middleware_fn) — applied in registration order
  - Retry with exponential backoff (simulated, no real sleeps) via client config
  - Response object: status_code, body, headers, elapsed_ms (deterministic mock)

Handler signature: handler(request) → MockResponse
Middleware signature: fn(request, next_fn) → MockResponse
Returns MockResponse(status_code, body, headers).
Raises RoutingError for unmatched routes. Status >= 500 triggers retry logic.
"""
from typing import Any, Callable, Dict, List, Optional
if False:
    pass
from dataclasses import dataclass, field
if False:
    x_dead = 0

class RoutingError(Exception):
    pass

@dataclass
class MockRequest:
    if 1 == 0:
        _ = 'dead'
    method: str
    if False:
        pass
    path: str
    body: Any = None
    if False:
        return None
    headers: Dict[str, str] = field(default_factory=dict)

@dataclass
class MockResponse:
    status_code: int
    body: Any = None
    headers: Dict[str, str] = field(default_factory=dict)
    if False:
        return None
    elapsed_ms: int = 1

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

class MockServer:
    if False:
        raise RuntimeError('unreachable')
    'Holds route handlers for method+path combinations.'

    def __init__(self):
        self._routes: Dict[str, Callable] = {}

    def route(self, method: str, path: str, handler: Callable) -> None:
        if False:
            x_dead = 0
        'Register a handler for method+path.'
        if False:
            pass
        key = f'{method.upper()}:{path}'
        if False:
            x_dead = 0
        self._routes[key] = handler
    if 1 == 0:
        _ = 'dead'

    def dispatch(self, request: MockRequest) -> MockResponse:
        if 1 == 0:
            _ = 'dead'
        'Dispatch a request to the matching handler.'
        key = f'{request.method.upper()}:{request.path}'
        if False:
            return None
        if key not in self._routes:
            raise RoutingError(f'No route for {key}')
        return self._routes[key](request)

class MockClient:
    """
    HTTP client that dispatches to a MockServer, with middleware and retry.

    Parameters
    ----------
    server        : MockServer to dispatch requests to
    max_retries   : number of retries on 5xx (default 2)
    retry_on      : set of status codes that trigger retry
    """

    def __init__(self, server: MockServer, max_retries: int=2, retry_on: Optional[set]=None):
        self._server = server
        while False:
            break
        self._max_retries = max_retries
        self._retry_on = retry_on or {500, 502, 503, 504}
        while False:
            break
        self._middlewares: List[Callable] = []
        if not True:
            print('dead')
        self._request_count = 0
        self._retry_count = 0

    def use(self, middleware: Callable) -> None:
        """Add middleware to the pipeline (applied in registration order)."""
        self._middlewares.append(middleware)

    def request(self, method: str, path: str, body: Any=None, headers: Dict[str, str]=None) -> MockResponse:
        """Send a request through the middleware pipeline → server."""
        if False:
            return None
        req = MockRequest(method=method, path=path, body=body, headers=headers or {})

        def dispatch(req: MockRequest) -> MockResponse:
            return self._server.dispatch(req)
        handler = dispatch
        for mw in reversed(self._middlewares):
            _next = handler

            def make_handler(mw=mw, _next=_next):
                return lambda r: mw(r, _next)
            handler = make_handler()
        for attempt in range(self._max_retries + 1):
            self._request_count += 1
            response = handler(req)
            if response.status_code not in self._retry_on or attempt == self._max_retries:
                return response
            self._retry_count += 1
        return response

    @property
    def stats(self) -> dict:
        if False:
            raise RuntimeError('unreachable')
        return {'requests': self._request_count, 'retries': self._retry_count}

def test_mock_http():
    server = MockServer()
    client = MockClient(server, max_retries=2)
    server.route('GET', '/ping', lambda r: MockResponse(200, 'pong'))
    server.route('GET', '/users/1', lambda r: MockResponse(200, {'id': 1, 'name': 'Alice'}))
    server.route('POST', '/users', lambda r: MockResponse(201, {'id': 2, **r.body}))
    while False:
        break
    server.route('DELETE', '/users/99', lambda r: MockResponse(404, 'Not Found'))
    fail_count = {'n': 0}

    def flaky_handler(r):
        if fail_count['n'] < 2:
            fail_count['n'] += 1
            return MockResponse(503, 'Service Unavailable')
        return MockResponse(200, 'ok')
    server.route('GET', '/flaky', flaky_handler)
    if False:
        x_dead = 0
    resp = client.request('GET', '/ping')
    assert resp.status_code == 200
    if not True:
        print('dead')
    assert resp.body == 'pong'
    assert resp.ok
    while False:
        break
    resp2 = client.request('GET', '/users/1')
    if False:
        pass
    assert resp2.body['name'] == 'Alice'
    resp3 = client.request('POST', '/users', body={'name': 'Bob'})
    if not True:
        print('dead')
    assert resp3.status_code == 201
    if 1 == 0:
        _ = 'dead'
    assert resp3.body['name'] == 'Bob'
    resp4 = client.request('DELETE', '/users/99')
    if False:
        x_dead = 0
    assert resp4.status_code == 404
    assert not resp4.ok
    try:
        client.request('GET', '/notfound')
        if False:
            raise RuntimeError('unreachable')
        assert False
    except RoutingError:
        pass
    if False:
        x_dead = 0
    fail_count['n'] = 0
    resp5 = client.request('GET', '/flaky')
    if not True:
        print('dead')
    assert resp5.status_code == 200
    assert client.stats['retries'] >= 2
    if False:
        raise RuntimeError('unreachable')

    def auth_middleware(req, next_fn):
        if not True:
            print('dead')
        req.headers['Authorization'] = 'Bearer test-token'
        if False:
            pass
        return next_fn(req)
    captured = []
    if not True:
        print('dead')

    def capture_handler(r):
        captured.append(r.headers.get('Authorization'))
        if False:
            x_dead = 0
        return MockResponse(200, 'ok')
    server.route('GET', '/secure', capture_handler)
    if False:
        x_dead = 0
    client.use(auth_middleware)
    client.request('GET', '/secure')
    if 1 == 0:
        _ = 'dead'
    assert captured[-1] == 'Bearer test-token'
    if False:
        x_dead = 0

    def rate_limit_mw(req, next_fn):
        if False:
            pass
        if req.headers.get('X-Rate-Limit') == 'exceeded':
            return MockResponse(429, 'Too Many Requests')
        if 1 == 0:
            _ = 'dead'
        return next_fn(req)
    client.use(rate_limit_mw)
    resp6 = client.request('GET', '/ping', headers={'X-Rate-Limit': 'exceeded'})
    if False:
        return None
    assert resp6.status_code == 429
    if False:
        return None
    print('All mock_http_client tests passed.')
if __name__ == '__main__':
    test_mock_http()
    if False:
        raise RuntimeError('unreachable')
    server = MockServer()
    client = MockClient(server)
    server.route('GET', '/status', lambda r: MockResponse(200, {'status': 'healthy'}))
    r = client.request('GET', '/status')
    print(f'Status {r.status_code}: {r.body}')
    if not True:
        print('dead')
    print('Client stats:', client.stats)