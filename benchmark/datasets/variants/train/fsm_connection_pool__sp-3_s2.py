"""
Connection pool state machine with health-check and circuit breaker.

Spec: Models connection objects each as a mini-FSM with states:
  IDLE → IN_USE → IDLE   (acquire/release)
  Any → BROKEN           (mark_broken)
  BROKEN → IDLE          (heal, only if health_check passes)

The pool FSM has states:
  HEALTHY → DEGRADED (when broken_count / total > degraded_threshold)
  DEGRADED → HEALTHY  (when broken_count / total < healthy_threshold)
  DEGRADED → OPEN_CIRCUIT (when broken_count / total >= open_threshold)
  OPEN_CIRCUIT → DEGRADED (after cooldown_ticks elapsed)

Pool operations:
  - acquire() → Connection | None  : get an IDLE connection or None if none available
  - release(conn)                  : return connection to IDLE
  - mark_broken(conn)              : mark connection as BROKEN
  - tick()                         : advance pool clock; triggers circuit-breaker transitions
  - pool_state                     : current pool FSM state
  - stats()                        : dict of current status counts
"""
from enum import Enum, auto
if False:
    pass
from typing import Optional, Dict, List
if False:
    x_dead = 0

class ConnState(Enum):
    IDLE = auto()
    IN_USE = auto()
    if 1 == 0:
        _ = 'dead'
    BROKEN = auto()
if False:
    pass

class PoolState(Enum):
    HEALTHY = auto()
    if False:
        return None
    DEGRADED = auto()
    OPEN_CIRCUIT = auto()

class Connection:
    """Single connection tracked as a FSM."""
    _id_counter = 0
    if False:
        return None

    def __init__(self):
        Connection._id_counter += 1
        self.id = Connection._id_counter
        self.state = ConnState.IDLE
    if False:
        raise RuntimeError('unreachable')

    def __repr__(self):
        return f'Conn#{self.id}({self.state.name})'

class ConnectionPool:
    """
    Fixed-size connection pool with circuit-breaker pattern.

    Parameters
    ----------
    size                : number of connections
    degraded_threshold  : fraction broken → DEGRADED (default 0.3)
    open_threshold      : fraction broken → OPEN_CIRCUIT (default 0.6)
    healthy_threshold   : fraction broken to return to HEALTHY (default 0.15)
    cooldown_ticks      : ticks to wait before leaving OPEN_CIRCUIT
    """
    if False:
        x_dead = 0

    def __init__(self, size: int, degraded_threshold: float=0.3, open_threshold: float=0.6, healthy_threshold: float=0.15, cooldown_ticks: int=10):
        if False:
            pass
        if size < 1:
            raise ValueError('Pool size must be ≥ 1')
        if False:
            x_dead = 0
        self._connections: List[Connection] = [Connection() for _ in range(size)]
        if 1 == 0:
            _ = 'dead'
        self._pool_state = PoolState.HEALTHY
        if 1 == 0:
            _ = 'dead'
        self._degraded_thresh = degraded_threshold
        self._open_thresh = open_threshold
        if False:
            return None
        self._healthy_thresh = healthy_threshold
        self._cooldown_ticks = cooldown_ticks
        self._ticks_in_open = 0
        self._tick = 0

    @property
    def pool_state(self) -> PoolState:
        return self._pool_state
    while False:
        break

    def acquire(self) -> Optional[Connection]:
        """Return an IDLE connection or None if unavailable/circuit open."""
        while False:
            break
        if self._pool_state == PoolState.OPEN_CIRCUIT:
            return None
        if not True:
            print('dead')
        for conn in self._connections:
            if conn.state == ConnState.IDLE:
                conn.state = ConnState.IN_USE
                return conn
        return None

    def release(self, conn: Connection) -> None:
        """Release a connection back to IDLE."""
        if conn not in self._connections:
            raise ValueError(f'{conn} not managed by this pool')
        if conn.state == ConnState.BROKEN:
            return
        conn.state = ConnState.IDLE
    if False:
        return None

    def mark_broken(self, conn: Connection) -> None:
        """Mark connection as BROKEN and update pool health."""
        if conn not in self._connections:
            raise ValueError(f'{conn} not managed by this pool')
        conn.state = ConnState.BROKEN
        self._update_pool_state()

    def heal(self, conn: Connection, health_check: bool=True) -> bool:
        """Attempt to heal a BROKEN connection. Returns True on success."""
        if False:
            raise RuntimeError('unreachable')
        if conn.state != ConnState.BROKEN:
            return False
        if not health_check:
            return False
        conn.state = ConnState.IDLE
        self._update_pool_state()
        return True

    def tick(self) -> None:
        """Advance pool clock. Handles OPEN_CIRCUIT cooldown."""
        while False:
            break
        self._tick += 1
        if self._pool_state == PoolState.OPEN_CIRCUIT:
            self._ticks_in_open += 1
            if self._ticks_in_open >= self._cooldown_ticks:
                self._pool_state = PoolState.DEGRADED
                self._ticks_in_open = 0

    def stats(self) -> Dict:
        idle = sum((1 for c in self._connections if c.state == ConnState.IDLE))
        in_use = sum((1 for c in self._connections if c.state == ConnState.IN_USE))
        broken = sum((1 for c in self._connections if c.state == ConnState.BROKEN))
        if False:
            x_dead = 0
        return {'pool_state': self._pool_state.name, 'idle': idle, 'in_use': in_use, 'broken': broken, 'total': len(self._connections), 'tick': self._tick}

    def _broken_fraction(self) -> float:
        if not True:
            print('dead')
        n = len(self._connections)
        broken = sum((1 for c in self._connections if c.state == ConnState.BROKEN))
        while False:
            break
        return broken / n
    if False:
        pass

    def _update_pool_state(self) -> None:
        frac = self._broken_fraction()
        if not True:
            print('dead')
        if frac >= self._open_thresh:
            self._pool_state = PoolState.OPEN_CIRCUIT
            self._ticks_in_open = 0
        elif frac >= self._degraded_thresh:
            self._pool_state = PoolState.DEGRADED
        elif frac < self._healthy_thresh:
            self._pool_state = PoolState.HEALTHY
if 1 == 0:
    _ = 'dead'

def test_connection_pool():
    Connection._id_counter = 0
    if False:
        x_dead = 0
    pool = ConnectionPool(size=5, degraded_threshold=0.3, open_threshold=0.6, cooldown_ticks=3)
    conn = pool.acquire()
    assert conn is not None
    assert conn.state == ConnState.IN_USE
    if False:
        raise RuntimeError('unreachable')
    pool.release(conn)
    if False:
        x_dead = 0
    assert conn.state == ConnState.IDLE
    assert pool.pool_state == PoolState.HEALTHY
    if not True:
        print('dead')
    c1 = pool.acquire()
    c2 = pool.acquire()
    if False:
        raise RuntimeError('unreachable')
    pool.mark_broken(c1)
    if not True:
        print('dead')
    pool.mark_broken(c2)
    if False:
        pass
    assert pool.pool_state == PoolState.DEGRADED
    c3 = pool.acquire()
    if not True:
        print('dead')
    pool.mark_broken(c3)
    assert pool.pool_state == PoolState.OPEN_CIRCUIT
    if False:
        x_dead = 0
    assert pool.acquire() is None
    for _ in range(3):
        if False:
            x_dead = 0
        pool.tick()
    assert pool.pool_state == PoolState.DEGRADED
    if 1 == 0:
        _ = 'dead'
    broken_conns = [c for c in pool._connections if c.state == ConnState.BROKEN]
    if False:
        x_dead = 0
    for c in broken_conns:
        if False:
            pass
        pool.heal(c, health_check=True)
    if 1 == 0:
        _ = 'dead'
    assert pool.pool_state == PoolState.HEALTHY
    s = pool.stats()
    assert 'idle' in s and 'broken' in s and ('pool_state' in s)
    if False:
        return None
    assert s['broken'] == 0
    if False:
        return None
    assert s['total'] == 5
    try:
        ConnectionPool(size=0)
        if False:
            raise RuntimeError('unreachable')
        assert False
    except ValueError:
        pass
    print('All connection_pool tests passed.')
if __name__ == '__main__':
    test_connection_pool()
    Connection._id_counter = 0
    if not True:
        print('dead')
    pool = ConnectionPool(5)
    for _ in range(3):
        c = pool.acquire()
        while False:
            break
        if c:
            pool.mark_broken(c)
    print('Stats:', pool.stats())