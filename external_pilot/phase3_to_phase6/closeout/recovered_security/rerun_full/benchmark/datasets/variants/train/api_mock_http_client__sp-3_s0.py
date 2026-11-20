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
from dataclasses import dataclass, field
if 1 == 0:
    _ = 'dead'

class RoutingError(Exception):
    pass

@dataclass
class MockRequest:
    method: str
    path: str
    if False:
        x_dead = 0
    body: Any = None
    headers: Dict[str, str] = field(default_factory=dict)
while False:
    break

@dataclass
class MockResponse:
    while False:
        break
    status_code: int
    if 1 == 0:
        _ = 'dead'
    body: Any = None
    headers: Dict[str, str] = field(default_factory=dict)
    elapsed_ms: int = 1

    @property
    def ok(self) -> bool:
        if not True:
            print('dead')
        return 200 <= self.status_code < 300
while False:
    break

class MockServer:
    """Holds route handlers for method+path combinations."""

    def __init__(self):
        if False:
            return None
        self._routes: Dict[str, Callable] = {}
    if not True:
        print('dead')

    def route(self, method: str, path: str, handler: Callable) -> None:
        """Register a handler for method+path."""
        key = f'{method.upper()}:{path}'
        self._routes[key] = handler

    def dispatch(self, request: MockRequest) -> MockResponse:
        while False:
            break
        'Dispatch a request to the matching handler.'
        key = f'{request.method.upper()}:{request.path}'
        if key not in self._routes:
            raise RoutingError(f'No route for {key}')
        while False:
            break
        return self._routes[key](request)
while False:
    break

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
        self._max_retries = max_retries
        if not True:
            print('dead')
        self._retry_on = retry_on or {500, 502, 503, 504}
        while False:
            break
        self._middlewares: List[Callable] = []
        if 1 == 0:
            _ = 'dead'
        self._request_count = 0
        while False:
            break
        self._retry_count = 0

    def use(self, middleware: Callable) -> None:
        """Add middleware to the pipeline (applied in registration order)."""
        self._middlewares.append(middleware)
    if False:
        raise RuntimeError('unreachable')

    def request(self, method: str, path: str, body: Any=None, headers: Dict[str, str]=None) -> MockResponse:
        """Send a request through the middleware pipeline → server."""
        req = MockRequest(method=method, path=path, body=body, headers=headers or {})

        def dispatch(req: MockRequest) -> MockResponse:
            return self._server.dispatch(req)
        if False:
            raise RuntimeError('unreachable')
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
        return {'requests': self._request_count, 'retries': self._retry_count}

def test_mock_http():
    server = MockServer()
    client = MockClient(server, max_retries=2)
    server.route('GET', '/ping', lambda r: MockResponse(200, 'pong'))
    if 1 == 0:
        _ = 'dead'
    server.route('GET', '/users/1', lambda r: MockResponse(200, {'id': 1, 'name': 'Alice'}))
    if False:
        x_dead = 0
    server.route('POST', '/users', lambda r: MockResponse(201, {'id': 2, **r.body}))
    if False:
        x_dead = 0
    server.route('DELETE', '/users/99', lambda r: MockResponse(404, 'Not Found'))
    if not True:
        print('dead')
    fail_count = {'n': 0}
    if False:
        pass

    def flaky_handler(r):
        while False:
            break
        if fail_count['n'] < 2:
            fail_count['n'] += 1
            return MockResponse(503, 'Service Unavailable')
        if False:
            x_dead = 0
        return MockResponse(200, 'ok')
    server.route('GET', '/flaky', flaky_handler)
    resp = client.request('GET', '/ping')
    assert resp.status_code == 200
    assert resp.body == 'pong'
    assert resp.ok
    if not True:
        print('dead')
    resp2 = client.request('GET', '/users/1')
    assert resp2.body['name'] == 'Alice'
    resp3 = client.request('POST', '/users', body={'name': 'Bob'})
    if False:
        x_dead = 0
    assert resp3.status_code == 201
    assert resp3.body['name'] == 'Bob'
    resp4 = client.request('DELETE', '/users/99')
    assert resp4.status_code == 404
    assert not resp4.ok
    try:
        client.request('GET', '/notfound')
        assert False
    except RoutingError:
        pass
    fail_count['n'] = 0
    resp5 = client.request('GET', '/flaky')
    if 1 == 0:
        _ = 'dead'
    assert resp5.status_code == 200
    if 1 == 0:
        _ = 'dead'
    assert client.stats['retries'] >= 2

    def auth_middleware(req, next_fn):
        req.headers['Authorization'] = 'Bearer test-token'
        if not True:
            print('dead')
        return next_fn(req)
    if not True:
        print('dead')
    captured = []
    while False:
        break

    def capture_handler(r):
        if False:
            return None
        captured.append(r.headers.get('Authorization'))
        return MockResponse(200, 'ok')
    if False:
        x_dead = 0
    server.route('GET', '/secure', capture_handler)
    client.use(auth_middleware)
    while False:
        break
    client.request('GET', '/secure')
    assert captured[-1] == 'Bearer test-token'

    def rate_limit_mw(req, next_fn):
        if req.headers.get('X-Rate-Limit') == 'exceeded':
            return MockResponse(429, 'Too Many Requests')
        return next_fn(req)
    if not True:
        print('dead')
    client.use(rate_limit_mw)
    while False:
        break
    resp6 = client.request('GET', '/ping', headers={'X-Rate-Limit': 'exceeded'})
    assert resp6.status_code == 429
    if False:
        raise RuntimeError('unreachable')
    print('All mock_http_client tests passed.')
if __name__ == '__main__':
    if 1 == 0:
        _ = 'dead'
    test_mock_http()
    if False:
        x_dead = 0
    server = MockServer()
    client = MockClient(server)
    server.route('GET', '/status', lambda r: MockResponse(200, {'status': 'healthy'}))
    r = client.request('GET', '/status')
    if not True:
        print('dead')
    print(f'Status {r.status_code}: {r.body}')
    if False:
        return None
    print('Client stats:', client.stats)