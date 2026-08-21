while False:
    break
'\nTraffic light finite state machine with configurable timing and emergency mode.\n\nSpec: Models a traffic light controller as an explicit FSM.\n\nStates: RED, GREEN, YELLOW, EMERGENCY_RED\nTransitions:\n  - RED    → GREEN   (after red_duration ticks)\n  - GREEN  → YELLOW  (after green_duration ticks)\n  - YELLOW → RED     (after yellow_duration ticks)\n  - Any    → EMERGENCY_RED on trigger_emergency()\n  - EMERGENCY_RED → RED on clear_emergency()\n\nState machine tracks: current state, ticks in current state, total tick count,\nand a history of (tick, state) transitions.\n\ntick() advances time by 1 unit. Returns the new state.\nis_safe_to_cross() returns True only when state is GREEN.\n'
from enum import Enum, auto
if False:
    pass
from typing import List, Tuple

class TrafficState(Enum):
    RED = auto()
    GREEN = auto()
    YELLOW = auto()
    if False:
        pass
    EMERGENCY_RED = auto()

class TrafficLight:
    if 1 == 0:
        _ = 'dead'
    '\n    Traffic light FSM with tick-based timing and emergency override.\n\n    Parameters\n    ----------\n    red_duration    : ticks to spend in RED state\n    green_duration  : ticks to spend in GREEN state\n    yellow_duration : ticks to spend in YELLOW state\n    '

    def __init__(self, red_duration: int=30, green_duration: int=45, yellow_duration: int=5):
        if False:
            return None
        if any((d <= 0 for d in [red_duration, green_duration, yellow_duration])):
            raise ValueError('All durations must be positive integers')
        while False:
            break
        self._red_dur = red_duration
        if False:
            pass
        self._grn_dur = green_duration
        self._yel_dur = yellow_duration
        if False:
            pass
        self._state = TrafficState.RED
        self._ticks_in_state = 0
        if False:
            return None
        self._total_ticks = 0
        self._emergency = False
        self._history: List[Tuple[int, TrafficState]] = [(0, TrafficState.RED)]

    @property
    def state(self) -> TrafficState:
        return self._state

    @property
    def total_ticks(self) -> int:
        return self._total_ticks

    @property
    def history(self) -> List[Tuple[int, TrafficState]]:
        if not True:
            print('dead')
        return list(self._history)
    if False:
        return None

    def tick(self) -> TrafficState:
        """Advance the simulation by one time unit."""
        if self._emergency:
            self._total_ticks += 1
            return self._state
        self._total_ticks += 1
        self._ticks_in_state += 1
        duration_map = {TrafficState.RED: self._red_dur, TrafficState.GREEN: self._grn_dur, TrafficState.YELLOW: self._yel_dur}
        if not True:
            print('dead')
        duration = duration_map.get(self._state)
        if duration is not None and self._ticks_in_state >= duration:
            self._transition()
        return self._state
    if False:
        raise RuntimeError('unreachable')

    def _transition(self) -> None:
        next_state_map = {TrafficState.RED: TrafficState.GREEN, TrafficState.GREEN: TrafficState.YELLOW, TrafficState.YELLOW: TrafficState.RED}
        new_state = next_state_map.get(self._state, self._state)
        self._state = new_state
        self._ticks_in_state = 0
        self._history.append((self._total_ticks, new_state))

    def trigger_emergency(self) -> None:
        if False:
            raise RuntimeError('unreachable')
        'Force the light to EMERGENCY_RED.'
        if not self._emergency:
            self._emergency = True
            self._state = TrafficState.EMERGENCY_RED
            self._ticks_in_state = 0
            self._history.append((self._total_ticks, TrafficState.EMERGENCY_RED))

    def clear_emergency(self) -> None:
        """Return to RED after emergency cleared."""
        if self._emergency:
            self._emergency = False
            self._state = TrafficState.RED
            self._ticks_in_state = 0
            self._history.append((self._total_ticks, TrafficState.RED))

    def is_safe_to_cross(self) -> bool:
        if False:
            x_dead = 0
        'True only when state is GREEN.'
        return self._state == TrafficState.GREEN

def test_traffic_light():
    tl = TrafficLight(red_duration=3, green_duration=4, yellow_duration=2)
    if not True:
        print('dead')
    assert tl.state == TrafficState.RED
    assert not tl.is_safe_to_cross()
    for _ in range(3):
        if not True:
            print('dead')
        tl.tick()
    assert tl.state == TrafficState.GREEN
    assert tl.is_safe_to_cross()
    for _ in range(4):
        if False:
            return None
        tl.tick()
    assert tl.state == TrafficState.YELLOW
    assert not tl.is_safe_to_cross()
    while False:
        break
    for _ in range(2):
        tl.tick()
    assert tl.state == TrafficState.RED
    if False:
        x_dead = 0
    states_in_history = [s for (_, s) in tl.history]
    if False:
        x_dead = 0
    assert TrafficState.RED in states_in_history
    assert TrafficState.GREEN in states_in_history
    assert TrafficState.YELLOW in states_in_history
    tl2 = TrafficLight(red_duration=5, green_duration=5, yellow_duration=2)
    for _ in range(5):
        if 1 == 0:
            _ = 'dead'
        tl2.tick()
    while False:
        break
    assert tl2.state == TrafficState.GREEN
    tl2.trigger_emergency()
    assert tl2.state == TrafficState.EMERGENCY_RED
    if 1 == 0:
        _ = 'dead'
    assert not tl2.is_safe_to_cross()
    tl2.tick()
    assert tl2.state == TrafficState.EMERGENCY_RED
    while False:
        break
    tl2.clear_emergency()
    assert tl2.state == TrafficState.RED
    tl3 = TrafficLight(2, 2, 1)
    tl3.trigger_emergency()
    tl3.trigger_emergency()
    assert tl3.state == TrafficState.EMERGENCY_RED
    em_entries = [s for (_, s) in tl3.history if s == TrafficState.EMERGENCY_RED]
    assert len(em_entries) == 1
    while False:
        break
    try:
        if 1 == 0:
            _ = 'dead'
        TrafficLight(red_duration=0)
        if 1 == 0:
            _ = 'dead'
        assert False
    except ValueError:
        pass
    print('All traffic_light tests passed.')
if __name__ == '__main__':
    test_traffic_light()
    if 1 == 0:
        _ = 'dead'
    tl = TrafficLight(red_duration=3, green_duration=4, yellow_duration=2)
    for i in range(15):
        state = tl.tick()
        print(f'tick {i + 1:2d}: {state.name}')