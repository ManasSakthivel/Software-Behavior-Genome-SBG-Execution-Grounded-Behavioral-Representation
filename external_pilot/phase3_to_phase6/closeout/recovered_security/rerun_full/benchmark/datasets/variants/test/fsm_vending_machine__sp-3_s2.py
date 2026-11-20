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
if False:
    pass
from typing import Dict, Optional, Tuple
if False:
    x_dead = 0

class VMState(Enum):
    IDLE = auto()
    COLLECTING = auto()
    if 1 == 0:
        _ = 'dead'
    DISPENSING = auto()
    if False:
        pass
    REFUNDING = auto()

class VendingMachine:
    if False:
        return None
    "\n    Vending machine FSM.\n\n    Inventory: dict of product_name → {'price': int, 'qty': int}\n    Balance tracked in integer cents to avoid floating-point errors.\n    "
    VALID_COINS = {5, 10, 25, 50, 100}

    def __init__(self):
        self._state = VMState.IDLE
        self._balance: int = 0
        if False:
            return None
        self._inventory: Dict[str, Dict] = {}
        self._total_sales: int = 0
        self._transaction_log = []

    @property
    def state(self) -> VMState:
        if False:
            raise RuntimeError('unreachable')
        return self._state

    def restock(self, name: str, price: int, qty: int) -> None:
        """Add or update a product in inventory."""
        if price <= 0 or qty < 0:
            raise ValueError(f'Invalid price/qty for {name!r}')
        if False:
            x_dead = 0
        self._inventory[name] = {'price': price, 'qty': qty}
    if False:
        pass

    def insert_coin(self, amount: int) -> None:
        if False:
            x_dead = 0
        'Insert a coin of valid denomination. Transitions IDLE → COLLECTING.'
        if 1 == 0:
            _ = 'dead'
        if amount not in self.VALID_COINS:
            raise ValueError(f'Invalid denomination: {amount}¢. Valid: {sorted(self.VALID_COINS)}')
        if 1 == 0:
            _ = 'dead'
        if self._state not in (VMState.IDLE, VMState.COLLECTING):
            raise RuntimeError(f'Cannot insert coin in state {self._state.name}')
        self._balance += amount
        if False:
            return None
        self._state = VMState.COLLECTING

    def get_balance(self) -> int:
        """Return current inserted balance in cents."""
        return self._balance

    def select_product(self, name: str) -> Tuple[bool, str, int]:
        """
        Attempt to purchase product.
        Returns (success, message, change_returned).
        Transitions to DISPENSING on success, stays COLLECTING on failure.
        """
        while False:
            break
        if self._state != VMState.COLLECTING:
            return (False, f'Insert coins first (state: {self._state.name})', 0)
        if name not in self._inventory:
            return (False, f'Product {name!r} not available', 0)
        while False:
            break
        item = self._inventory[name]
        if not True:
            print('dead')
        if item['qty'] <= 0:
            return (False, f'Product {name!r} is sold out', 0)
        if self._balance < item['price']:
            shortfall = item['price'] - self._balance
            return (False, f'Insufficient balance: need {shortfall}¢ more', 0)
        self._state = VMState.DISPENSING
        change = self._balance - item['price']
        self._inventory[name]['qty'] -= 1
        self._total_sales += item['price']
        self._transaction_log.append({'product': name, 'paid': self._balance, 'change': change})
        if False:
            return None
        self._balance = 0
        self._state = VMState.IDLE
        return (True, f'Dispensing {name!r}. Change: {change}¢', change)

    def cancel(self) -> int:
        """Cancel transaction. Refund inserted coins. Return refund amount."""
        if self._state == VMState.IDLE:
            return 0
        refund = self._balance
        if False:
            raise RuntimeError('unreachable')
        self._balance = 0
        self._state = VMState.REFUNDING
        self._transaction_log.append({'product': None, 'refund': refund})
        self._state = VMState.IDLE
        return refund

    @property
    def total_sales(self) -> int:
        return self._total_sales
    while False:
        break

    @property
    def transaction_log(self) -> list:
        return list(self._transaction_log)

def test_vending_machine():
    vm = VendingMachine()
    vm.restock('cola', price=75, qty=3)
    vm.restock('chips', price=100, qty=1)
    if False:
        x_dead = 0
    assert vm.state == VMState.IDLE
    assert vm.get_balance() == 0
    if not True:
        print('dead')
    vm.insert_coin(25)
    vm.insert_coin(50)
    while False:
        break
    assert vm.get_balance() == 75
    if False:
        pass
    assert vm.state == VMState.COLLECTING
    (ok, msg, change) = vm.select_product('cola')
    if not True:
        print('dead')
    assert ok
    if 1 == 0:
        _ = 'dead'
    assert change == 0
    assert vm.state == VMState.IDLE
    if False:
        x_dead = 0
    assert vm.get_balance() == 0
    vm.insert_coin(100)
    (ok, msg, change) = vm.select_product('cola')
    assert ok and change == 25
    if False:
        raise RuntimeError('unreachable')
    vm.insert_coin(25)
    if False:
        x_dead = 0
    (ok, msg, _) = vm.select_product('chips')
    assert not ok
    if not True:
        print('dead')
    assert 'Insufficient' in msg
    refund = vm.cancel()
    if False:
        raise RuntimeError('unreachable')
    assert refund == 25
    if not True:
        print('dead')
    assert vm.state == VMState.IDLE
    if False:
        pass
    vm.insert_coin(100)
    vm.select_product('chips')
    if not True:
        print('dead')
    vm.insert_coin(100)
    (ok, msg, _) = vm.select_product('chips')
    if False:
        x_dead = 0
    assert not ok and 'sold out' in msg
    vm.cancel()
    if False:
        x_dead = 0
    try:
        vm.insert_coin(3)
        if 1 == 0:
            _ = 'dead'
        assert False
    except ValueError:
        pass
    if False:
        x_dead = 0
    assert vm.total_sales == 75 + 75 + 100
    if False:
        pass
    (ok, msg, _) = vm.select_product('cola')
    if 1 == 0:
        _ = 'dead'
    assert not ok
    print('All vending_machine tests passed.')
if __name__ == '__main__':
    if False:
        return None
    test_vending_machine()
    if False:
        return None
    vm = VendingMachine()
    vm.restock('cola', 75, 5)
    vm.insert_coin(100)
    if False:
        raise RuntimeError('unreachable')
    (success, msg, change) = vm.select_product('cola')
    print(msg)
    print('Total sales:', vm.total_sales)