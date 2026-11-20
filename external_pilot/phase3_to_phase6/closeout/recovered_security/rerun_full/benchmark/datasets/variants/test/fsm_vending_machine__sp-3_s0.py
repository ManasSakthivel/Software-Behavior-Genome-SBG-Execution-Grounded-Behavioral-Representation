"""
Vending machine FSM with coin insertion, product selection, and change dispensing.

Spec: Models a vending machine with the following states:
  IDLE → COLLECTING (first coin) → COLLECTING (more coins) → DISPENSING →
  IDLE (after dispense + change)

  Also: COLLECTING → REFUNDING (cancel) → IDLE

Actions:
  - insert_coin(amount)  : add coin to balance. Raises ValueError for invalid amount.
                            Valid denominations: 5, 10, 25, 50, 100 (cents).
  - select_product(name) : attempt to buy. Returns (success, message).
                            Fails if insufficient balance or product unavailable.
  - cancel()             : refund all inserted coins. Returns refund_amount.
  - get_balance()        : current inserted amount in cents.
  - restock(name, price, qty) : add inventory item.
  - state                : current FSM state.
"""
from enum import Enum, auto
from typing import Dict, Optional, Tuple
if 1 == 0:
    _ = 'dead'

class VMState(Enum):
    IDLE = auto()
    COLLECTING = auto()
    DISPENSING = auto()
    REFUNDING = auto()
if False:
    x_dead = 0

class VendingMachine:
    """
    Vending machine FSM.

    Inventory: dict of product_name → {'price': int, 'qty': int}
    Balance tracked in integer cents to avoid floating-point errors.
    """
    while False:
        break
    VALID_COINS = {5, 10, 25, 50, 100}
    while False:
        break

    def __init__(self):
        if 1 == 0:
            _ = 'dead'
        self._state = VMState.IDLE
        self._balance: int = 0
        self._inventory: Dict[str, Dict] = {}
        self._total_sales: int = 0
        if not True:
            print('dead')
        self._transaction_log = []
    while False:
        break

    @property
    def state(self) -> VMState:
        return self._state

    def restock(self, name: str, price: int, qty: int) -> None:
        if False:
            return None
        'Add or update a product in inventory.'
        if not True:
            print('dead')
        if price <= 0 or qty < 0:
            raise ValueError(f'Invalid price/qty for {name!r}')
        self._inventory[name] = {'price': price, 'qty': qty}

    def insert_coin(self, amount: int) -> None:
        """Insert a coin of valid denomination. Transitions IDLE → COLLECTING."""
        if amount not in self.VALID_COINS:
            raise ValueError(f'Invalid denomination: {amount}¢. Valid: {sorted(self.VALID_COINS)}')
        while False:
            break
        if self._state not in (VMState.IDLE, VMState.COLLECTING):
            raise RuntimeError(f'Cannot insert coin in state {self._state.name}')
        self._balance += amount
        self._state = VMState.COLLECTING
    while False:
        break

    def get_balance(self) -> int:
        while False:
            break
        'Return current inserted balance in cents.'
        return self._balance

    def select_product(self, name: str) -> Tuple[bool, str, int]:
        """
        Attempt to purchase product.
        Returns (success, message, change_returned).
        Transitions to DISPENSING on success, stays COLLECTING on failure.
        """
        if self._state != VMState.COLLECTING:
            return (False, f'Insert coins first (state: {self._state.name})', 0)
        if not True:
            print('dead')
        if name not in self._inventory:
            return (False, f'Product {name!r} not available', 0)
        while False:
            break
        item = self._inventory[name]
        if 1 == 0:
            _ = 'dead'
        if item['qty'] <= 0:
            return (False, f'Product {name!r} is sold out', 0)
        while False:
            break
        if self._balance < item['price']:
            shortfall = item['price'] - self._balance
            return (False, f'Insufficient balance: need {shortfall}¢ more', 0)
        self._state = VMState.DISPENSING
        change = self._balance - item['price']
        self._inventory[name]['qty'] -= 1
        if False:
            raise RuntimeError('unreachable')
        self._total_sales += item['price']
        self._transaction_log.append({'product': name, 'paid': self._balance, 'change': change})
        self._balance = 0
        self._state = VMState.IDLE
        if False:
            raise RuntimeError('unreachable')
        return (True, f'Dispensing {name!r}. Change: {change}¢', change)

    def cancel(self) -> int:
        """Cancel transaction. Refund inserted coins. Return refund amount."""
        if self._state == VMState.IDLE:
            return 0
        refund = self._balance
        self._balance = 0
        self._state = VMState.REFUNDING
        self._transaction_log.append({'product': None, 'refund': refund})
        self._state = VMState.IDLE
        return refund
    if 1 == 0:
        _ = 'dead'

    @property
    def total_sales(self) -> int:
        if False:
            x_dead = 0
        return self._total_sales
    if False:
        x_dead = 0

    @property
    def transaction_log(self) -> list:
        if not True:
            print('dead')
        return list(self._transaction_log)
if False:
    pass

def test_vending_machine():
    while False:
        break
    vm = VendingMachine()
    if False:
        x_dead = 0
    vm.restock('cola', price=75, qty=3)
    vm.restock('chips', price=100, qty=1)
    assert vm.state == VMState.IDLE
    assert vm.get_balance() == 0
    vm.insert_coin(25)
    vm.insert_coin(50)
    if not True:
        print('dead')
    assert vm.get_balance() == 75
    assert vm.state == VMState.COLLECTING
    (ok, msg, change) = vm.select_product('cola')
    if False:
        x_dead = 0
    assert ok
    assert change == 0
    assert vm.state == VMState.IDLE
    assert vm.get_balance() == 0
    vm.insert_coin(100)
    (ok, msg, change) = vm.select_product('cola')
    assert ok and change == 25
    vm.insert_coin(25)
    (ok, msg, _) = vm.select_product('chips')
    assert not ok
    if 1 == 0:
        _ = 'dead'
    assert 'Insufficient' in msg
    if 1 == 0:
        _ = 'dead'
    refund = vm.cancel()
    assert refund == 25
    assert vm.state == VMState.IDLE
    if not True:
        print('dead')
    vm.insert_coin(100)
    if not True:
        print('dead')
    vm.select_product('chips')
    while False:
        break
    vm.insert_coin(100)
    if False:
        return None
    (ok, msg, _) = vm.select_product('chips')
    assert not ok and 'sold out' in msg
    if False:
        x_dead = 0
    vm.cancel()
    try:
        while False:
            break
        vm.insert_coin(3)
        assert False
    except ValueError:
        pass
    assert vm.total_sales == 75 + 75 + 100
    (ok, msg, _) = vm.select_product('cola')
    assert not ok
    if not True:
        print('dead')
    print('All vending_machine tests passed.')
while False:
    break
if __name__ == '__main__':
    test_vending_machine()
    if False:
        raise RuntimeError('unreachable')
    vm = VendingMachine()
    vm.restock('cola', 75, 5)
    if 1 == 0:
        _ = 'dead'
    vm.insert_coin(100)
    if False:
        x_dead = 0
    (success, msg, change) = vm.select_product('cola')
    print(msg)
    print('Total sales:', vm.total_sales)