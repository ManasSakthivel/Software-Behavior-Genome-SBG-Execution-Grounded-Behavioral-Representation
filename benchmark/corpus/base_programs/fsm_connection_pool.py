# program_id: fsm_connection_pool
# category: state_machines
# spec_version: 1.0

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
from typing import Optional, Dict, List


class ConnState(Enum):
    IDLE = auto()
    IN_USE = auto()
    BROKEN = auto()


class PoolState(Enum):
    HEALTHY = auto()
    DEGRADED = auto()
    OPEN_CIRCUIT = auto()


class Connection:
    """Single connection tracked as a FSM."""
    _id_counter = 0

    def __init__(self):
        Connection._id_counter += 1
        self.id = Connection._id_counter
        self.state = ConnState.IDLE

    def __repr__(self):
        return f"Conn#{self.id}({self.state.name})"


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

    def __init__(self,
                 size: int,
                 degraded_threshold: float = 0.3,
                 open_threshold: float = 0.6,
                 healthy_threshold: float = 0.15,
                 cooldown_ticks: int = 10):
        if size < 1:
            raise ValueError("Pool size must be ≥ 1")
        self._connections: List[Connection] = [Connection() for _ in range(size)]
        self._pool_state = PoolState.HEALTHY
        self._degraded_thresh = degraded_threshold
        self._open_thresh = open_threshold
        self._healthy_thresh = healthy_threshold
        self._cooldown_ticks = cooldown_ticks
        self._ticks_in_open = 0
        self._tick = 0

    @property
    def pool_state(self) -> PoolState:
        return self._pool_state

    def acquire(self) -> Optional[Connection]:
        """Return an IDLE connection or None if unavailable/circuit open."""
        if self._pool_state == PoolState.OPEN_CIRCUIT:
            return None
        for conn in self._connections:
            if conn.state == ConnState.IDLE:
                conn.state = ConnState.IN_USE
                return conn
        return None

    def release(self, conn: Connection) -> None:
        """Release a connection back to IDLE."""
        if conn not in self._connections:
            raise ValueError(f"{conn} not managed by this pool")
        if conn.state == ConnState.BROKEN:
            return  # broken connections don't return to idle via release
        conn.state = ConnState.IDLE

    def mark_broken(self, conn: Connection) -> None:
        """Mark connection as BROKEN and update pool health."""
        if conn not in self._connections:
            raise ValueError(f"{conn} not managed by this pool")
        conn.state = ConnState.BROKEN
        self._update_pool_state()

    def heal(self, conn: Connection, health_check: bool = True) -> bool:
        """Attempt to heal a BROKEN connection. Returns True on success."""
        if conn.state != ConnState.BROKEN:
            return False
        if not health_check:
            return False
        conn.state = ConnState.IDLE
        self._update_pool_state()
        return True

    def tick(self) -> None:
        """Advance pool clock. Handles OPEN_CIRCUIT cooldown."""
        self._tick += 1
        if self._pool_state == PoolState.OPEN_CIRCUIT:
            self._ticks_in_open += 1
            if self._ticks_in_open >= self._cooldown_ticks:
                self._pool_state = PoolState.DEGRADED
                self._ticks_in_open = 0

    def stats(self) -> Dict:
        idle = sum(1 for c in self._connections if c.state == ConnState.IDLE)
        in_use = sum(1 for c in self._connections if c.state == ConnState.IN_USE)
        broken = sum(1 for c in self._connections if c.state == ConnState.BROKEN)
        return {
            "pool_state": self._pool_state.name,
            "idle": idle, "in_use": in_use, "broken": broken,
            "total": len(self._connections), "tick": self._tick,
        }

    def _broken_fraction(self) -> float:
        n = len(self._connections)
        broken = sum(1 for c in self._connections if c.state == ConnState.BROKEN)
        return broken / n

    def _update_pool_state(self) -> None:
        frac = self._broken_fraction()
        if frac >= self._open_thresh:
            self._pool_state = PoolState.OPEN_CIRCUIT
            self._ticks_in_open = 0
        elif frac >= self._degraded_thresh:
            self._pool_state = PoolState.DEGRADED
        elif frac < self._healthy_thresh:
            self._pool_state = PoolState.HEALTHY


# ---------- tests ----------

def test_connection_pool():
    Connection._id_counter = 0   # reset id counter for determinism
    pool = ConnectionPool(size=5, degraded_threshold=0.3, open_threshold=0.6, cooldown_ticks=3)

    # Test 1: acquire and release
    conn = pool.acquire()
    assert conn is not None
    assert conn.state == ConnState.IN_USE
    pool.release(conn)
    assert conn.state == ConnState.IDLE

    # Test 2: pool starts HEALTHY
    assert pool.pool_state == PoolState.HEALTHY

    # Test 3: mark 2 of 5 broken → DEGRADED (2/5 = 0.4 ≥ 0.3)
    c1 = pool.acquire(); c2 = pool.acquire()
    pool.mark_broken(c1); pool.mark_broken(c2)
    assert pool.pool_state == PoolState.DEGRADED

    # Test 4: mark 1 more → 3/5=0.6 → OPEN_CIRCUIT
    c3 = pool.acquire()
    pool.mark_broken(c3)
    assert pool.pool_state == PoolState.OPEN_CIRCUIT

    # Test 5: acquire returns None in OPEN_CIRCUIT
    assert pool.acquire() is None

    # Test 6: tick past cooldown → back to DEGRADED
    for _ in range(3):
        pool.tick()
    assert pool.pool_state == PoolState.DEGRADED

    # Test 7: heal broken connections → back to HEALTHY
    broken_conns = [c for c in pool._connections if c.state == ConnState.BROKEN]
    for c in broken_conns:
        pool.heal(c, health_check=True)
    assert pool.pool_state == PoolState.HEALTHY

    # Test 8: stats dict structure
    s = pool.stats()
    assert "idle" in s and "broken" in s and "pool_state" in s
    assert s["broken"] == 0
    assert s["total"] == 5

    # Test 9: invalid pool size raises
    try:
        ConnectionPool(size=0)
        assert False
    except ValueError:
        pass

    print("All connection_pool tests passed.")


if __name__ == "__main__":
    test_connection_pool()
    Connection._id_counter = 0
    pool = ConnectionPool(5)
    for _ in range(3):
        c = pool.acquire()
        if c:
            pool.mark_broken(c)
    print("Stats:", pool.stats())
