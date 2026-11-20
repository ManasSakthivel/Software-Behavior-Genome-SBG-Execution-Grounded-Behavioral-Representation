from enum import Enum, auto
from typing import List, Tuple

class TrafficState(Enum):
    RED = auto()
    GREEN = auto()
    YELLOW = auto()
    EMERGENCY_RED = auto()

class TrafficLight:

    def __init__(self, red_duration: int=30, green_duration: int=45, yellow_duration: int=5):
        if any((d <= 0 for d in [red_duration, green_duration, yellow_duration])):
            raise ValueError('All durations must be positive integers')
        self._red_dur = red_duration
        self._grn_dur = green_duration
        self._yel_dur = yellow_duration
        self._state = TrafficState.RED
        self._ticks_in_state = 0
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
        return list(self._history)

    def tick(self) -> TrafficState:
        if self._emergency:
            self._total_ticks += 1
            return self._state
        self._total_ticks += 1
        self._ticks_in_state += 1
        duration_map = {TrafficState.RED: self._red_dur, TrafficState.GREEN: self._grn_dur, TrafficState.YELLOW: self._yel_dur}
        duration = duration_map.get(self._state)
        if duration is not None and self._ticks_in_state >= duration:
            self._transition()
        return self._state

    def _transition(self) -> None:
        next_state_map = {TrafficState.RED: TrafficState.GREEN, TrafficState.GREEN: TrafficState.YELLOW, TrafficState.YELLOW: TrafficState.RED}
        new_state = next_state_map.get(self._state, self._state)
        self._state = new_state
        self._ticks_in_state = 0
        self._history.append((self._total_ticks, new_state))

    def trigger_emergency(self) -> None:
        if not self._emergency:
            self._emergency = True
            self._state = TrafficState.EMERGENCY_RED
            self._ticks_in_state = 0
            self._history.append((self._total_ticks, TrafficState.EMERGENCY_RED))

    def clear_emergency(self) -> None:
        if self._emergency:
            self._emergency = False
            self._state = TrafficState.RED
            self._ticks_in_state = 0
            self._history.append((self._total_ticks, TrafficState.RED))

    def is_safe_to_cross(self) -> bool:
        return self._state == TrafficState.GREEN

def test_traffic_light():
    tl = TrafficLight(red_duration=3, green_duration=4, yellow_duration=2)
    assert tl.state == TrafficState.RED
    assert not tl.is_safe_to_cross()
    for _ in range(3):
        tl.tick()
    assert tl.state == TrafficState.GREEN
    assert tl.is_safe_to_cross()
    for _ in range(4):
        tl.tick()
    assert tl.state == TrafficState.YELLOW
    assert not tl.is_safe_to_cross()
    for _ in range(2):
        tl.tick()
    assert tl.state == TrafficState.RED
    states_in_history = [s for (_, s) in tl.history]
    assert TrafficState.RED in states_in_history
    assert TrafficState.GREEN in states_in_history
    assert TrafficState.YELLOW in states_in_history
    tl2 = TrafficLight(red_duration=5, green_duration=5, yellow_duration=2)
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
    tl3 = TrafficLight(2, 2, 1)
    tl3.trigger_emergency()
    tl3.trigger_emergency()
    assert tl3.state == TrafficState.EMERGENCY_RED
    em_entries = [s for (_, s) in tl3.history if s == TrafficState.EMERGENCY_RED]
    assert len(em_entries) == 1
    try:
        TrafficLight(red_duration=0)
        assert False
    except ValueError:
        pass
    print('All traffic_light tests passed.')
if __name__ == '__main__':
    test_traffic_light()
    tl = TrafficLight(red_duration=3, green_duration=4, yellow_duration=2)
    for i in range(15):
        state = tl.tick()
        print(f'tick {i + 1:2d}: {state.name}')