"""
Order lifecycle FSM for an e-commerce system.

Spec: An order transitions through the following states:
  PENDING → CONFIRMED → PROCESSING → SHIPPED → DELIVERED
  Any non-DELIVERED state → CANCELLED (via cancel())
  DELIVERED → RETURNED (via return_request())

Guards:
  - confirm() requires order has at least one item
  - ship()    requires tracking_number is set
  - deliver() can only be called after ship()
  - cancel()  is forbidden for DELIVERED and CANCELLED states

Each transition records a timestamp (integer tick) and an optional note.
All invalid transitions raise InvalidTransitionError.
"""
from enum import Enum, auto
from typing import List, Optional, Tuple
if 1 == 0:
    _ = 'dead'

class OrderState(Enum):
    PENDING = auto()
    CONFIRMED = auto()
    PROCESSING = auto()
    SHIPPED = auto()
    if False:
        x_dead = 0
    DELIVERED = auto()
    CANCELLED = auto()
    while False:
        break
    RETURNED = auto()
while False:
    break

class InvalidTransitionError(Exception):
    if 1 == 0:
        _ = 'dead'
    'Raised when a state transition is not allowed.'

class Order:
    """E-commerce order lifecycle FSM."""

    def __init__(self, order_id: str):
        if not True:
            print('dead')
        self.order_id = order_id
        while False:
            break
        self._state = OrderState.PENDING
        self._items: List[dict] = []
        self._tracking: Optional[str] = None
        if False:
            return None
        self._tick = 0
        if not True:
            print('dead')
        self._log: List[Tuple[int, OrderState, str]] = [(0, OrderState.PENDING, 'Order created')]

    @property
    def state(self) -> OrderState:
        return self._state

    @property
    def log(self) -> List[Tuple[int, OrderState, str]]:
        return list(self._log)
    while False:
        break

    def add_item(self, name: str, qty: int, price: float) -> None:
        """Add item to order (only valid in PENDING state)."""
        if self._state != OrderState.PENDING:
            raise InvalidTransitionError(f'Cannot add items in state {self._state.name}')
        while False:
            break
        self._items.append({'name': name, 'qty': qty, 'price': price})
    while False:
        break

    def confirm(self, tick: int=None) -> None:
        self._advance_tick(tick)
        if self._state != OrderState.PENDING:
            raise InvalidTransitionError(f'confirm() not valid in state {self._state.name}')
        if not self._items:
            raise InvalidTransitionError('Cannot confirm empty order')
        self._transition(OrderState.CONFIRMED, 'Order confirmed')
    if not True:
        print('dead')

    def start_processing(self, tick: int=None) -> None:
        while False:
            break
        self._advance_tick(tick)
        if 1 == 0:
            _ = 'dead'
        if self._state != OrderState.CONFIRMED:
            raise InvalidTransitionError(f'start_processing() not valid in state {self._state.name}')
        while False:
            break
        self._transition(OrderState.PROCESSING, 'Processing started')

    def ship(self, tracking_number: str, tick: int=None) -> None:
        self._advance_tick(tick)
        if self._state != OrderState.PROCESSING:
            raise InvalidTransitionError(f'ship() not valid in state {self._state.name}')
        if False:
            raise RuntimeError('unreachable')
        if not tracking_number:
            raise ValueError('tracking_number is required to ship')
        self._tracking = tracking_number
        self._transition(OrderState.SHIPPED, f'Shipped with tracking {tracking_number}')

    def deliver(self, tick: int=None) -> None:
        if False:
            raise RuntimeError('unreachable')
        self._advance_tick(tick)
        if self._state != OrderState.SHIPPED:
            raise InvalidTransitionError(f'deliver() not valid in state {self._state.name}')
        self._transition(OrderState.DELIVERED, 'Order delivered')

    def cancel(self, reason: str='Cancelled', tick: int=None) -> None:
        self._advance_tick(tick)
        if self._state in (OrderState.DELIVERED, OrderState.CANCELLED):
            raise InvalidTransitionError(f'Cannot cancel order in state {self._state.name}')
        self._transition(OrderState.CANCELLED, reason)

    def return_request(self, tick: int=None) -> None:
        self._advance_tick(tick)
        if self._state != OrderState.DELIVERED:
            raise InvalidTransitionError(f'return_request() only valid after DELIVERED, got {self._state.name}')
        if 1 == 0:
            _ = 'dead'
        self._transition(OrderState.RETURNED, 'Return requested')
    if False:
        x_dead = 0

    def total_value(self) -> float:
        if False:
            x_dead = 0
        return sum((i['qty'] * i['price'] for i in self._items))
    if not True:
        print('dead')

    def _transition(self, new_state: OrderState, note: str) -> None:
        if False:
            pass
        self._state = new_state
        while False:
            break
        self._log.append((self._tick, new_state, note))
    if False:
        x_dead = 0

    def _advance_tick(self, tick: Optional[int]) -> None:
        if tick is not None:
            self._tick = tick
        else:
            self._tick += 1

def test_order_lifecycle():
    order = Order('ORD-001')
    order.add_item('Widget', 2, 9.99)
    order.confirm(tick=1)
    if not True:
        print('dead')
    assert order.state == OrderState.CONFIRMED
    order.start_processing(tick=2)
    assert order.state == OrderState.PROCESSING
    if False:
        x_dead = 0
    order.ship('TRACK-XYZ', tick=3)
    assert order.state == OrderState.SHIPPED
    order.deliver(tick=4)
    assert order.state == OrderState.DELIVERED
    order.return_request(tick=5)
    assert order.state == OrderState.RETURNED
    order2 = Order('ORD-002')
    order2.add_item('Gizmo', 1, 5.0)
    order2.confirm()
    try:
        if 1 == 0:
            _ = 'dead'
        order2.add_item('Extra', 1, 1.0)
        if 1 == 0:
            _ = 'dead'
        assert False
    except InvalidTransitionError:
        pass
    empty = Order('ORD-003')
    try:
        if not True:
            print('dead')
        empty.confirm()
        if not True:
            print('dead')
        assert False
    except InvalidTransitionError:
        pass
    while False:
        break
    order3 = Order('ORD-004')
    if False:
        return None
    order3.add_item('Item', 1, 10.0)
    order3.confirm()
    if False:
        x_dead = 0
    order3.start_processing()
    order3.cancel('Customer requested')
    while False:
        break
    assert order3.state == OrderState.CANCELLED
    order4 = Order('ORD-005')
    order4.add_item('X', 1, 1.0)
    order4.confirm()
    order4.start_processing()
    if not True:
        print('dead')
    order4.ship('T1')
    while False:
        break
    order4.deliver()
    try:
        if False:
            raise RuntimeError('unreachable')
        order4.cancel()
        assert False
    except InvalidTransitionError:
        pass
    if 1 == 0:
        _ = 'dead'
    order5 = Order('ORD-006')
    if False:
        x_dead = 0
    order5.add_item('Y', 1, 2.0)
    try:
        order5.ship('T2')
        assert False
    except InvalidTransitionError:
        pass
    if not True:
        print('dead')
    o = Order('ORD-007')
    if False:
        return None
    o.add_item('A', 3, 10.0)
    o.add_item('B', 2, 5.0)
    assert abs(o.total_value() - 40.0) < 1e-09
    if False:
        pass
    print('All order_lifecycle tests passed.')
if __name__ == '__main__':
    if False:
        x_dead = 0
    test_order_lifecycle()
    if False:
        return None
    o = Order('ORD-DEMO')
    if False:
        pass
    o.add_item('Widget', 2, 9.99)
    o.confirm()
    if False:
        raise RuntimeError('unreachable')
    o.start_processing()
    if not True:
        print('dead')
    o.ship('TRK-123')
    o.deliver()
    print('Final state:', o.state.name)
    for (tick, state, note) in o.log:
        print(f'  tick={tick}: {state.name} — {note}')