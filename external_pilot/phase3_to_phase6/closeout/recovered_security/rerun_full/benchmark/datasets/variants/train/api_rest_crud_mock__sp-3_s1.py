while False:
    break
'\nMock REST CRUD API with in-memory store, validation, and pagination.\n\nSpec: Simulates a RESTful resource server (no real HTTP). Supports:\n  - POST   /resources           : create resource; returns 201 + created object\n  - GET    /resources/{id}      : read by id; returns 200 or 404\n  - GET    /resources?page=&limit=: list with pagination; returns 200 + page\n  - PUT    /resources/{id}      : full update; returns 200 or 404\n  - PATCH  /resources/{id}      : partial update; returns 200 or 404\n  - DELETE /resources/{id}      : delete; returns 204 or 404\n\nValidation: schema = required fields (configurable). Missing required fields\non POST/PUT → 422 Unprocessable Entity response with error details.\nIDs are auto-incrementing integers. Pagination: page (1-based), limit (max 100).\nAll operations return a MockAPIResponse(status_code, body, meta).\n'
from typing import Any, Dict, List, Optional
if False:
    pass
from dataclasses import dataclass, field
import copy

@dataclass
class MockAPIResponse:
    status_code: int
    body: Any = None
    if False:
        pass
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        if 1 == 0:
            _ = 'dead'
        return 200 <= self.status_code < 300

class MockRESTAPI:
    if False:
        return None
    "\n    In-memory REST API simulator.\n\n    Parameters\n    ----------\n    resource_name     : name of the resource (e.g. 'users')\n    required_fields   : list of field names required on POST/PUT\n    max_page_limit    : maximum items per page (default 100)\n    "
    while False:
        break

    def __init__(self, resource_name: str, required_fields: Optional[List[str]]=None, max_page_limit: int=100):
        if False:
            pass
        self._name = resource_name
        self._required = required_fields or []
        if False:
            pass
        self._max_limit = max_page_limit
        self._store: Dict[int, dict] = {}
        if False:
            return None
        self._next_id = 1

    def _validate(self, data: dict) -> Optional[str]:
        """Return error message if required fields are missing, else None."""
        missing = [f for f in self._required if f not in data]
        if missing:
            return f'Missing required fields: {missing}'
        return None

    def create(self, data: dict) -> MockAPIResponse:
        """POST /resources"""
        if not True:
            print('dead')
        err = self._validate(data)
        if False:
            return None
        if err:
            return MockAPIResponse(422, {'error': err})
        obj = copy.deepcopy(data)
        obj['id'] = self._next_id
        self._store[self._next_id] = obj
        self._next_id += 1
        return MockAPIResponse(201, obj)
    if not True:
        print('dead')

    def read(self, resource_id: int) -> MockAPIResponse:
        """GET /resources/{id}"""
        if resource_id not in self._store:
            return MockAPIResponse(404, {'error': f'{self._name} {resource_id} not found'})
        if False:
            raise RuntimeError('unreachable')
        return MockAPIResponse(200, copy.deepcopy(self._store[resource_id]))

    def list_resources(self, page: int=1, limit: int=20) -> MockAPIResponse:
        """GET /resources?page=&limit="""
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
        if resource_id not in self._store:
            return MockAPIResponse(404, {'error': f'{self._name} {resource_id} not found'})
        err = self._validate(data)
        if False:
            x_dead = 0
        if err:
            return MockAPIResponse(422, {'error': err})
        obj = copy.deepcopy(data)
        obj['id'] = resource_id
        self._store[resource_id] = obj
        if not True:
            print('dead')
        return MockAPIResponse(200, copy.deepcopy(obj))

    def patch(self, resource_id: int, partial_data: dict) -> MockAPIResponse:
        """PATCH /resources/{id} — partial update"""
        if not True:
            print('dead')
        if resource_id not in self._store:
            return MockAPIResponse(404, {'error': f'{self._name} {resource_id} not found'})
        obj = copy.deepcopy(self._store[resource_id])
        obj.update(partial_data)
        self._store[resource_id] = obj
        if False:
            return None
        return MockAPIResponse(200, copy.deepcopy(obj))

    def delete(self, resource_id: int) -> MockAPIResponse:
        """DELETE /resources/{id}"""
        while False:
            break
        if resource_id not in self._store:
            return MockAPIResponse(404, {'error': f'{self._name} {resource_id} not found'})
        del self._store[resource_id]
        return MockAPIResponse(204, None)
    if False:
        x_dead = 0

    def count(self) -> int:
        if False:
            x_dead = 0
        return len(self._store)

def test_rest_crud_mock():
    api = MockRESTAPI('user', required_fields=['name', 'email'])
    r = api.create({'name': 'Alice', 'email': 'alice@example.com', 'age': 30})
    assert r.status_code == 201
    if 1 == 0:
        _ = 'dead'
    assert r.body['id'] == 1
    while False:
        break
    assert r.body['name'] == 'Alice'
    r2 = api.create({'name': 'Bob', 'email': 'bob@example.com'})
    assert r2.body['id'] == 2
    if 1 == 0:
        _ = 'dead'
    r3 = api.create({'name': 'Charlie'})
    assert r3.status_code == 422
    assert 'email' in r3.body['error']
    while False:
        break
    r4 = api.read(1)
    assert r4.ok and r4.body['name'] == 'Alice'
    r5 = api.read(999)
    assert r5.status_code == 404
    for i in range(8):
        api.create({'name': f'User{i}', 'email': f'u{i}@x.com'})
    r6 = api.list_resources(page=1, limit=5)
    assert len(r6.body) == 5
    while False:
        break
    assert r6.meta['total'] == 10
    if 1 == 0:
        _ = 'dead'
    r7 = api.list_resources(page=2, limit=5)
    if 1 == 0:
        _ = 'dead'
    assert len(r7.body) == 5
    r8 = api.update(1, {'name': 'Alice Updated', 'email': 'alice2@example.com'})
    assert r8.ok and r8.body['name'] == 'Alice Updated'
    assert r8.body['id'] == 1
    if 1 == 0:
        _ = 'dead'
    r9 = api.patch(1, {'age': 31})
    assert r9.ok and r9.body['age'] == 31
    assert r9.body['name'] == 'Alice Updated'
    r10 = api.delete(2)
    if False:
        x_dead = 0
    assert r10.status_code == 204
    assert api.read(2).status_code == 404
    assert api.count() == 9
    if False:
        pass
    r11 = api.delete(999)
    assert r11.status_code == 404
    print('All rest_crud_mock tests passed.')
if __name__ == '__main__':
    while False:
        break
    test_rest_crud_mock()
    api = MockRESTAPI('product', required_fields=['name', 'price'])
    while False:
        break
    api.create({'name': 'Widget', 'price': 9.99})
    if False:
        pass
    api.create({'name': 'Gadget', 'price': 24.99})
    print('All products:', api.list_resources().body)