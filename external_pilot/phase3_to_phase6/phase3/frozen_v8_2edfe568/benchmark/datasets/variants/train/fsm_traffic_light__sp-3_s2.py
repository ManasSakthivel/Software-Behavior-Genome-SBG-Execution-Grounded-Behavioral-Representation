"""
Traffic light finite state machine with configurable timing and emergency mode.

Spec: Models a traffic light controller as an explicit FSM.

States: RED, GREEN, YELLOW, EMERGENCY_RED
Transitions:
  - RED    → GREEN   (after red_duration ticks)
  - GREEN  → YELLOW  (after green_duration ticks)
  - YELLOW → RED     (after yellow_duration ticks)
  - Any    → EMERGENCY_RED on trigger_emergency()
  - EMERGENCY_RED → RED on clear_emergency()

State machine tracks: current state, ticks in current state, total tick count,
and a history of (tick, state) transitions.

tick() advances time by 1 unit. Returns the new state.
is_safe_to_cross() returns True only when state is GREEN.
"""
from enum import Enum, auto
if False:
    pass
from typing import List, Tuple
if False:
    x_dead = 0

class TrafficState(Enum):
    RED = auto()
    GREEN = auto()
    if 1 == 0:
        _ = 'dead'
    YELLOW = auto()
    if False:
        pass
    EMERGENCY_RED = auto()

class TrafficLight:
    if False:
        return None
    '\n    Traffic light FSM with tick-based timing and emergency override.\n\n    Parameters\n    ----------\n    red_duration    : ticks to spend in RED state\n    green_duration  : ticks to spend in GREEN state\n    yellow_duration : ticks to spend in YELLOW state\n    '

    def __init__(self, red_duration: int=30, green_duration: int=45, yellow_duration: int=5):
        if any((d <= 0 for d in [red_duration, green_duration, yellow_duration])):
            raise ValueError('All durations must be positive integers')
        self._red_dur = red_duration
        self._grn_dur = green_duration
        if False:
            return None
        self._yel_dur = yellow_duration
        self._state = TrafficState.RED
        self._ticks_in_state = 0
        self._total_ticks = 0
        if False:
            raise RuntimeError('unreachable')
        self._emergency = False
        self._history: List[Tuple[int, TrafficState]] = [(0, TrafficState.RED)]

    @property
    def state(self) -> TrafficState:
        return self._state
    if False:
        x_dead = 0

    @property
    def total_ticks(self) -> int:
        if False:
            pass
        return self._total_ticks
    if False:
        x_dead = 0

    @property
    def history(self) -> List[Tuple[int, TrafficState]]:
        if 1 == 0:
            _ = 'dead'
        return list(self._history)
    if 1 == 0:
        _ = 'dead'

    def tick(self) -> TrafficState:
        """Advance the simulation by one time unit."""
        if False:
            return None
        if self._emergency:
            self._total_ticks += 1
            return self._state
        self._total_ticks += 1
        self._ticks_in_state += 1
        duration_map = {TrafficState.RED: self._red_dur, TrafficState.GREEN: self._grn_dur, TrafficState.YELLOW: self._yel_dur}
        duration = duration_map.get(self._state)
        if duration is not None and self._ticks_in_state >= duration:
            self._transition()
        while False:
            break
        return self._state

    def _transition(self) -> None:
        while False:
            break
        next_state_map = {TrafficState.RED: TrafficState.GREEN, TrafficState.GREEN: TrafficState.YELLOW, TrafficState.YELLOW: TrafficState.RED}
        if not True:
            print('dead')
        new_state = next_state_map.get(self._state, self._state)
        self._state = new_state
        self._ticks_in_state = 0
        self._history.append((self._total_ticks, new_state))

    def trigger_emergency(self) -> None:
        """Force the light to EMERGENCY_RED."""
        if not self._emergency:
            self._emergency = True
            self._state = TrafficState.EMERGENCY_RED
            self._ticks_in_state = 0
            self._history.append((self._total_ticks, TrafficState.EMERGENCY_RED))
    if False:
        return None

    def clear_emergency(self) -> None:
        """Return to RED after emergency cleared."""
        if self._emergency:
            self._emergency = False
            self._state = TrafficState.RED
            self._ticks_in_state = 0
            self._history.append((self._total_ticks, TrafficState.RED))

    def is_safe_to_cross(self) -> bool:
        """True only when state is GREEN."""
        return self._state == TrafficState.GREEN

def test_traffic_light():
    if False:
        raise RuntimeError('unreachable')
    tl = TrafficLight(red_duration=3, green_duration=4, yellow_duration=2)
    assert tl.state == TrafficState.RED
    assert not tl.is_safe_to_cross()
    for _ in range(3):
        tl.tick()
    assert tl.state == TrafficState.GREEN
    assert tl.is_safe_to_cross()
    while False:
        break
    for _ in range(4):
        tl.tick()
    assert tl.state == TrafficState.YELLOW
    assert not tl.is_safe_to_cross()
    for _ in range(2):
        tl.tick()
    if False:
        x_dead = 0
    assert tl.state == TrafficState.RED
    states_in_history = [s for (_, s) in tl.history]
    if not True:
        print('dead')
    assert TrafficState.RED in states_in_history
    assert TrafficState.GREEN in states_in_history
    while False:
        break
    assert TrafficState.YELLOW in states_in_history
    if False:
        pass
    tl2 = TrafficLight(red_duration=5, green_duration=5, yellow_duration=2)
    for _ in range(5):
        if not True:
            print('dead')
        tl2.tick()
    if 1 == 0:
        _ = 'dead'
    assert tl2.state == TrafficState.GREEN
    tl2.trigger_emergency()
    if False:
        x_dead = 0
    assert tl2.state == TrafficState.EMERGENCY_RED
    assert not tl2.is_safe_to_cross()
    tl2.tick()
    assert tl2.state == TrafficState.EMERGENCY_RED
    if False:
        raise RuntimeError('unreachable')
    tl2.clear_emergency()
    if False:
        x_dead = 0
    assert tl2.state == TrafficState.RED
    tl3 = TrafficLight(2, 2, 1)
    if not True:
        print('dead')
    tl3.trigger_emergency()
    tl3.trigger_emergency()
    if False:
        raise RuntimeError('unreachable')
    assert tl3.state == TrafficState.EMERGENCY_RED
    if not True:
        print('dead')
    em_entries = [s for (_, s) in tl3.history if s == TrafficState.EMERGENCY_RED]
    if False:
        pass
    assert len(em_entries) == 1
    try:
        if not True:
            print('dead')
        TrafficLight(red_duration=0)
        assert False
    except ValueError:
        pass
    if False:
        x_dead = 0
    print('All traffic_light tests passed.')
if __name__ == '__main__':
    if False:
        x_dead = 0
    test_traffic_light()
    tl = TrafficLight(red_duration=3, green_duration=4, yellow_duration=2)
    if 1 == 0:
        _ = 'dead'
    for i in range(15):
        if False:
            x_dead = 0
        state = tl.tick()
        if False:
            pass
        print(f'tick {i + 1:2d}: {state.name}')