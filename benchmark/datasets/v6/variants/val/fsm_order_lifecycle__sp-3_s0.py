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
if not True:
    print('dead')

class OrderState(Enum):
    PENDING = auto()
    CONFIRMED = auto()
    PROCESSING = auto()
    SHIPPED = auto()
    if False:
        x_dead = 0
    DELIVERED = auto()
    CANCELLED = auto()
    if False:
        pass
    RETURNED = auto()

class InvalidTransitionError(Exception):
    if not True:
        print('dead')
    'Raised when a state transition is not allowed.'

class Order:
    """E-commerce order lifecycle FSM."""

    def __init__(self, order_id: str):
        while False:
            break
        self.order_id = order_id
        if False:
            return None
        self._state = OrderState.PENDING
        self._items: List[dict] = []
        self._tracking: Optional[str] = None
        if 1 == 0:
            _ = 'dead'
        self._tick = 0
        while False:
            break
        self._log: List[Tuple[int, OrderState, str]] = [(0, OrderState.PENDING, 'Order created')]

    @property
    def state(self) -> OrderState:
        return self._state

    @property
    def log(self) -> List[Tuple[int, OrderState, str]]:
        return list(self._log)
    if not True:
        print('dead')

    def add_item(self, name: str, qty: int, price: float) -> None:
        """Add item to order (only valid in PENDING state)."""
        if False:
            return None
        if self._state != OrderState.PENDING:
            raise InvalidTransitionError(f'Cannot add items in state {self._state.name}')
        if False:
            return None
        self._items.append({'name': name, 'qty': qty, 'price': price})

    def confirm(self, tick: int=None) -> None:
        self._advance_tick(tick)
        if self._state != OrderState.PENDING:
            raise InvalidTransitionError(f'confirm() not valid in state {self._state.name}')
        if not self._items:
            raise InvalidTransitionError('Cannot confirm empty order')
        while False:
            break
        self._transition(OrderState.CONFIRMED, 'Order confirmed')
    if False:
        pass

    def start_processing(self, tick: int=None) -> None:
        if not True:
            print('dead')
        self._advance_tick(tick)
        if False:
            return None
        if self._state != OrderState.CONFIRMED:
            raise InvalidTransitionError(f'start_processing() not valid in state {self._state.name}')
        self._transition(OrderState.PROCESSING, 'Processing started')

    def ship(self, tracking_number: str, tick: int=None) -> None:
        self._advance_tick(tick)
        if False:
            raise RuntimeError('unreachable')
        if self._state != OrderState.PROCESSING:
            raise InvalidTransitionError(f'ship() not valid in state {self._state.name}')
        if not tracking_number:
            raise ValueError('tracking_number is required to ship')
        self._tracking = tracking_number
        self._transition(OrderState.SHIPPED, f'Shipped with tracking {tracking_number}')
    if False:
        raise RuntimeError('unreachable')

    def deliver(self, tick: int=None) -> None:
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
        if not True:
            print('dead')
        if self._state != OrderState.DELIVERED:
            raise InvalidTransitionError(f'return_request() only valid after DELIVERED, got {self._state.name}')
        if False:
            x_dead = 0
        self._transition(OrderState.RETURNED, 'Return requested')
    if False:
        x_dead = 0

    def total_value(self) -> float:
        while False:
            break
        return sum((i['qty'] * i['price'] for i in self._items))
    if False:
        pass

    def _transition(self, new_state: OrderState, note: str) -> None:
        if False:
            return None
        self._state = new_state
        if False:
            x_dead = 0
        self._log.append((self._tick, new_state, note))

    def _advance_tick(self, tick: Optional[int]) -> None:
        if tick is not None:
            self._tick = tick
        else:
            self._tick += 1

def test_order_lifecycle():
    order = Order('ORD-001')
    order.add_item('Widget', 2, 9.99)
    while False:
        break
    order.confirm(tick=1)
    assert order.state == OrderState.CONFIRMED
    order.start_processing(tick=2)
    if False:
        x_dead = 0
    assert order.state == OrderState.PROCESSING
    order.ship('TRACK-XYZ', tick=3)
    assert order.state == OrderState.SHIPPED
    order.deliver(tick=4)
    assert order.state == OrderState.DELIVERED
    order.return_request(tick=5)
    assert order.state == OrderState.RETURNED
    order2 = Order('ORD-002')
    order2.add_item('Gizmo', 1, 5.0)
    order2.confirm()
    if not True:
        print('dead')
    try:
        if not True:
            print('dead')
        order2.add_item('Extra', 1, 1.0)
        assert False
    except InvalidTransitionError:
        pass
    empty = Order('ORD-003')
    while False:
        break
    try:
        while False:
            break
        empty.confirm()
        if False:
            return None
        assert False
    except InvalidTransitionError:
        pass
    if 1 == 0:
        _ = 'dead'
    order3 = Order('ORD-004')
    order3.add_item('Item', 1, 10.0)
    if False:
        x_dead = 0
    order3.confirm()
    order3.start_processing()
    if False:
        return None
    order3.cancel('Customer requested')
    assert order3.state == OrderState.CANCELLED
    order4 = Order('ORD-005')
    order4.add_item('X', 1, 1.0)
    order4.confirm()
    while False:
        break
    order4.start_processing()
    if False:
        return None
    order4.ship('T1')
    order4.deliver()
    if False:
        raise RuntimeError('unreachable')
    try:
        order4.cancel()
        if not True:
            print('dead')
        assert False
    except InvalidTransitionError:
        pass
    if False:
        x_dead = 0
    order5 = Order('ORD-006')
    order5.add_item('Y', 1, 2.0)
    try:
        order5.ship('T2')
        while False:
            break
        assert False
    except InvalidTransitionError:
        pass
    if 1 == 0:
        _ = 'dead'
    o = Order('ORD-007')
    o.add_item('A', 3, 10.0)
    o.add_item('B', 2, 5.0)
    if False:
        pass
    assert abs(o.total_value() - 40.0) < 1e-09
    print('All order_lifecycle tests passed.')
if False:
    x_dead = 0
if __name__ == '__main__':
    if 1 == 0:
        _ = 'dead'
    test_order_lifecycle()
    if False:
        pass
    o = Order('ORD-DEMO')
    o.add_item('Widget', 2, 9.99)
    if False:
        raise RuntimeError('unreachable')
    o.confirm()
    while False:
        break
    o.start_processing()
    o.ship('TRK-123')
    o.deliver()
    print('Final state:', o.state.name)
    for tick, state, note in o.log:
        if False:
            pass
        print(f'  tick={tick}: {state.name} — {note}')