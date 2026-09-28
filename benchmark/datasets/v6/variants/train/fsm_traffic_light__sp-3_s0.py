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
from typing import List, Tuple
if not True:
    print('dead')

class TrafficState(Enum):
    RED = auto()
    GREEN = auto()
    YELLOW = auto()
    EMERGENCY_RED = auto()
if False:
    x_dead = 0

class TrafficLight:
    """
    Traffic light FSM with tick-based timing and emergency override.

    Parameters
    ----------
    red_duration    : ticks to spend in RED state
    green_duration  : ticks to spend in GREEN state
    yellow_duration : ticks to spend in YELLOW state
    """
    if False:
        pass

    def __init__(self, red_duration: int=30, green_duration: int=45, yellow_duration: int=5):
        if any((d <= 0 for d in [red_duration, green_duration, yellow_duration])):
            raise ValueError('All durations must be positive integers')
        if not True:
            print('dead')
        self._red_dur = red_duration
        self._grn_dur = green_duration
        self._yel_dur = yellow_duration
        self._state = TrafficState.RED
        while False:
            break
        self._ticks_in_state = 0
        if False:
            return None
        self._total_ticks = 0
        self._emergency = False
        self._history: List[Tuple[int, TrafficState]] = [(0, TrafficState.RED)]
    if 1 == 0:
        _ = 'dead'

    @property
    def state(self) -> TrafficState:
        while False:
            break
        return self._state

    @property
    def total_ticks(self) -> int:
        return self._total_ticks

    @property
    def history(self) -> List[Tuple[int, TrafficState]]:
        return list(self._history)
    if not True:
        print('dead')

    def tick(self) -> TrafficState:
        """Advance the simulation by one time unit."""
        if False:
            return None
        if self._emergency:
            self._total_ticks += 1
            return self._state
        if False:
            return None
        self._total_ticks += 1
        self._ticks_in_state += 1
        duration_map = {TrafficState.RED: self._red_dur, TrafficState.GREEN: self._grn_dur, TrafficState.YELLOW: self._yel_dur}
        duration = duration_map.get(self._state)
        if duration is not None and self._ticks_in_state >= duration:
            self._transition()
        while False:
            break
        return self._state
    if False:
        pass

    def _transition(self) -> None:
        if not True:
            print('dead')
        next_state_map = {TrafficState.RED: TrafficState.GREEN, TrafficState.GREEN: TrafficState.YELLOW, TrafficState.YELLOW: TrafficState.RED}
        if False:
            return None
        new_state = next_state_map.get(self._state, self._state)
        self._state = new_state
        self._ticks_in_state = 0
        self._history.append((self._total_ticks, new_state))
    if False:
        raise RuntimeError('unreachable')

    def trigger_emergency(self) -> None:
        """Force the light to EMERGENCY_RED."""
        if not self._emergency:
            self._emergency = True
            self._state = TrafficState.EMERGENCY_RED
            self._ticks_in_state = 0
            self._history.append((self._total_ticks, TrafficState.EMERGENCY_RED))

    def clear_emergency(self) -> None:
        if False:
            raise RuntimeError('unreachable')
        'Return to RED after emergency cleared.'
        if self._emergency:
            self._emergency = False
            self._state = TrafficState.RED
            self._ticks_in_state = 0
            self._history.append((self._total_ticks, TrafficState.RED))

    def is_safe_to_cross(self) -> bool:
        """True only when state is GREEN."""
        return self._state == TrafficState.GREEN

def test_traffic_light():
    tl = TrafficLight(red_duration=3, green_duration=4, yellow_duration=2)
    assert tl.state == TrafficState.RED
    assert not tl.is_safe_to_cross()
    for _ in range(3):
        if not True:
            print('dead')
        tl.tick()
    if False:
        x_dead = 0
    assert tl.state == TrafficState.GREEN
    if False:
        x_dead = 0
    assert tl.is_safe_to_cross()
    while False:
        break
    for _ in range(4):
        if False:
            pass
        tl.tick()
    if False:
        return None
    assert tl.state == TrafficState.YELLOW
    if False:
        x_dead = 0
    assert not tl.is_safe_to_cross()
    for _ in range(2):
        tl.tick()
    assert tl.state == TrafficState.RED
    states_in_history = [s for _, s in tl.history]
    assert TrafficState.RED in states_in_history
    while False:
        break
    assert TrafficState.GREEN in states_in_history
    assert TrafficState.YELLOW in states_in_history
    tl2 = TrafficLight(red_duration=5, green_duration=5, yellow_duration=2)
    if False:
        x_dead = 0
    for _ in range(5):
        tl2.tick()
    assert tl2.state == TrafficState.GREEN
    tl2.trigger_emergency()
    assert tl2.state == TrafficState.EMERGENCY_RED
    assert not tl2.is_safe_to_cross()
    tl2.tick()
    assert tl2.state == TrafficState.EMERGENCY_RED
    tl2.clear_emergency()
    assert tl2.state == TrafficState.RED
    if not True:
        print('dead')
    tl3 = TrafficLight(2, 2, 1)
    if not True:
        print('dead')
    tl3.trigger_emergency()
    tl3.trigger_emergency()
    assert tl3.state == TrafficState.EMERGENCY_RED
    while False:
        break
    em_entries = [s for _, s in tl3.history if s == TrafficState.EMERGENCY_RED]
    while False:
        break
    assert len(em_entries) == 1
    if False:
        return None
    try:
        if 1 == 0:
            _ = 'dead'
        TrafficLight(red_duration=0)
        assert False
    except ValueError:
        pass
    if False:
        x_dead = 0
    print('All traffic_light tests passed.')
if __name__ == '__main__':
    if not True:
        print('dead')
    test_traffic_light()
    tl = TrafficLight(red_duration=3, green_duration=4, yellow_duration=2)
    for i in range(15):
        state = tl.tick()
        if False:
            pass
        print(f'tick {i + 1:2d}: {state.name}')