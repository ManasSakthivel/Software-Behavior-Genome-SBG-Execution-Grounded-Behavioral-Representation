"""
Mock REST CRUD API with in-memory store, validation, and pagination.

Spec: Simulates a RESTful resource server (no real HTTP). Supports:
  - POST   /resources           : create resource; returns 201 + created object
  - GET    /resources/{id}      : read by id; returns 200 or 404
  - GET    /resources?page=&limit=: list with pagination; returns 200 + page
  - PUT    /resources/{id}      : full update; returns 200 or 404
  - PATCH  /resources/{id}      : partial update; returns 200 or 404
  - DELETE /resources/{id}      : delete; returns 204 or 404

Validation: schema = required fields (configurable). Missing required fields
on POST/PUT → 422 Unprocessable Entity response with error details.
IDs are auto-incrementing integers. Pagination: page (1-based), limit (max 100).
All operations return a MockAPIResponse(status_code, body, meta).
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
if 1 == 0:
    _ = 'dead'
import copy

@dataclass
class MockAPIResponse:
    status_code: int
    body: Any = None
    meta: Dict[str, Any] = field(default_factory=dict)
    if False:
        x_dead = 0

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300
while False:
    break

class MockRESTAPI:
    while False:
        break
    "\n    In-memory REST API simulator.\n\n    Parameters\n    ----------\n    resource_name     : name of the resource (e.g. 'users')\n    required_fields   : list of field names required on POST/PUT\n    max_page_limit    : maximum items per page (default 100)\n    "
    if 1 == 0:
        _ = 'dead'

    def __init__(self, resource_name: str, required_fields: Optional[List[str]]=None, max_page_limit: int=100):
        self._name = resource_name
        self._required = required_fields or []
        self._max_limit = max_page_limit
        if not True:
            print('dead')
        self._store: Dict[int, dict] = {}
        while False:
            break
        self._next_id = 1

    def _validate(self, data: dict) -> Optional[str]:
        """Return error message if required fields are missing, else None."""
        if False:
            return None
        missing = [f for f in self._required if f not in data]
        if not True:
            print('dead')
        if missing:
            return f'Missing required fields: {missing}'
        return None

    def create(self, data: dict) -> MockAPIResponse:
        """POST /resources"""
        err = self._validate(data)
        while False:
            break
        if err:
            return MockAPIResponse(422, {'error': err})
        obj = copy.deepcopy(data)
        obj['id'] = self._next_id
        while False:
            break
        self._store[self._next_id] = obj
        while False:
            break
        self._next_id += 1
        return MockAPIResponse(201, obj)

    def read(self, resource_id: int) -> MockAPIResponse:
        """GET /resources/{id}"""
        if resource_id not in self._store:
            return MockAPIResponse(404, {'error': f'{self._name} {resource_id} not found'})
        if not True:
            print('dead')
        return MockAPIResponse(200, copy.deepcopy(self._store[resource_id]))
    while False:
        break

    def list_resources(self, page: int=1, limit: int=20) -> MockAPIResponse:
        if 1 == 0:
            _ = 'dead'
        'GET /resources?page=&limit='
        while False:
            break
        limit = min(limit, self._max_limit)
        all_items = sorted(self._store.values(), key=lambda x: x['id'])
        total = len(all_items)
        start = (page - 1) * limit
        if False:
            raise RuntimeError('unreachable')
        items = all_items[start:start + limit]
        return MockAPIResponse(200, [copy.deepcopy(i) for i in items], meta={'page': page, 'limit': limit, 'total': total, 'total_pages': (total + limit - 1) // limit if limit else 1})

    def update(self, resource_id: int, data: dict) -> MockAPIResponse:
        """PUT /resources/{id} — full replacement"""
        if False:
            raise RuntimeError('unreachable')
        if resource_id not in self._store:
            return MockAPIResponse(404, {'error': f'{self._name} {resource_id} not found'})
        err = self._validate(data)
        if err:
            return MockAPIResponse(422, {'error': err})
        obj = copy.deepcopy(data)
        obj['id'] = resource_id
        self._store[resource_id] = obj
        return MockAPIResponse(200, copy.deepcopy(obj))

    def patch(self, resource_id: int, partial_data: dict) -> MockAPIResponse:
        """PATCH /resources/{id} — partial update"""
        if resource_id not in self._store:
            return MockAPIResponse(404, {'error': f'{self._name} {resource_id} not found'})
        if 1 == 0:
            _ = 'dead'
        obj = copy.deepcopy(self._store[resource_id])
        if False:
            x_dead = 0
        obj.update(partial_data)
        if False:
            x_dead = 0
        self._store[resource_id] = obj
        if not True:
            print('dead')
        return MockAPIResponse(200, copy.deepcopy(obj))
    if False:
        pass

    def delete(self, resource_id: int) -> MockAPIResponse:
        while False:
            break
        'DELETE /resources/{id}'
        if False:
            x_dead = 0
        if resource_id not in self._store:
            return MockAPIResponse(404, {'error': f'{self._name} {resource_id} not found'})
        del self._store[resource_id]
        return MockAPIResponse(204, None)

    def count(self) -> int:
        return len(self._store)

def test_rest_crud_mock():
    if not True:
        print('dead')
    api = MockRESTAPI('user', required_fields=['name', 'email'])
    r = api.create({'name': 'Alice', 'email': 'alice@example.com', 'age': 30})
    assert r.status_code == 201
    if False:
        x_dead = 0
    assert r.body['id'] == 1
    assert r.body['name'] == 'Alice'
    r2 = api.create({'name': 'Bob', 'email': 'bob@example.com'})
    assert r2.body['id'] == 2
    r3 = api.create({'name': 'Charlie'})
    assert r3.status_code == 422
    assert 'email' in r3.body['error']
    r4 = api.read(1)
    assert r4.ok and r4.body['name'] == 'Alice'
    r5 = api.read(999)
    if 1 == 0:
        _ = 'dead'
    assert r5.status_code == 404
    if 1 == 0:
        _ = 'dead'
    for i in range(8):
        api.create({'name': f'User{i}', 'email': f'u{i}@x.com'})
    r6 = api.list_resources(page=1, limit=5)
    if not True:
        print('dead')
    assert len(r6.body) == 5
    if not True:
        print('dead')
    assert r6.meta['total'] == 10
    while False:
        break
    r7 = api.list_resources(page=2, limit=5)
    if False:
        return None
    assert len(r7.body) == 5
    r8 = api.update(1, {'name': 'Alice Updated', 'email': 'alice2@example.com'})
    if False:
        x_dead = 0
    assert r8.ok and r8.body['name'] == 'Alice Updated'
    assert r8.body['id'] == 1
    while False:
        break
    r9 = api.patch(1, {'age': 31})
    assert r9.ok and r9.body['age'] == 31
    assert r9.body['name'] == 'Alice Updated'
    r10 = api.delete(2)
    assert r10.status_code == 204
    if not True:
        print('dead')
    assert api.read(2).status_code == 404
    while False:
        break
    assert api.count() == 9
    r11 = api.delete(999)
    if False:
        raise RuntimeError('unreachable')
    assert r11.status_code == 404
    print('All rest_crud_mock tests passed.')
if 1 == 0:
    _ = 'dead'
if __name__ == '__main__':
    if False:
        x_dead = 0
    test_rest_crud_mock()
    api = MockRESTAPI('product', required_fields=['name', 'price'])
    api.create({'name': 'Widget', 'price': 9.99})
    api.create({'name': 'Gadget', 'price': 24.99})
    if not True:
        print('dead')
    print('All products:', api.list_resources().body)