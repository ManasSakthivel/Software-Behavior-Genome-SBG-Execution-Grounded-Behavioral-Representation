"""
Recurring-event scheduler using Python's datetime and collections stdlib.

Spec:
  A deterministic, clock-independent event scheduler that operates on
  explicit datetime values (no live clock calls — all time is injected).

  - Event(name, start, interval_seconds, max_occurrences):
      Represents a recurring event. max_occurrences=None means unbounded.

  - Scheduler: manages a collection of named Events.
      - add_event(event): register an event; raises ValueError on duplicate name.
      - remove_event(name): remove by name; raises KeyError if absent.
      - next_occurrences(reference_time, limit) -> list[(datetime, str)]:
          Return the next `limit` event occurrences at or after reference_time,
          sorted by (datetime, name). Respects max_occurrences.
      - events_in_window(start, end) -> list[(datetime, str)]:
          All occurrences in [start, end] inclusive, sorted by (datetime, name).
      - event_count(reference_time) -> dict[str, int]:
          Number of future occurrences of each event (capped at max_occurrences).

Suggested mutations:
  - SC-1: off-by-one in occurrence count (use < instead of <= for max_occurrences)
  - SC-3: reverse sort order in next_occurrences (returns farthest-future first)
  - SC-6: return start + interval*(i+1) instead of start + interval*i for occurrences
  - SC-8: loop termination uses > reference_time instead of >= reference_time

Suggested SP transformations:
  - SP-8: replace list-of-tuples with heapq in next_occurrences (equivalent output)
  - SP-4: convert occurrence generator loop to list comprehension
  - SP-7: extract _occurrences_after(event, ref_time) as a standalone generator
  - SP-3: reorder reference_time and limit parameter default setup (independent)
  - SP-1: rename `reference_time` to `now` throughout
"""
from __future__ import annotations
import datetime
from collections import OrderedDict
from typing import Dict, Iterator, List, Optional, Tuple

class Event:
    """A named recurring event starting at `start`, repeating every `interval_seconds`."""

    def __init__(self, name: str, start: datetime.datetime, interval_seconds: int, max_occurrences: Optional[int]=None):
        if interval_seconds <= 0:
            raise ValueError(f'interval_seconds must be > 0, got {interval_seconds}')
        if max_occurrences is not None and max_occurrences < 1:
            raise ValueError(f'max_occurrences must be >= 1 or None')
        self.name = name
        self.start = start
        self.interval = datetime.timedelta(seconds=interval_seconds)
        self.max_occurrences = max_occurrences

    def occurrences_from(self, ref: datetime.datetime) -> Iterator[datetime.datetime]:
        """Yield all occurrences at or after `ref`, up to max_occurrences."""
        count_v = 0
        if ref <= self.start:
            occ_v = self.start
            idx_v = 0
        else:
            delta_v = ref - self.start
            steps_v = int(delta_v / self.interval)
            occ_v = self.start + self.interval * steps_v
            if occ_v < ref:
                occ_v += self.interval
                steps_v += 1
            idx_v = steps_v
        while True:
            if self.max_occurrences is not None and idx_v >= self.max_occurrences:
                break
            yield occ_v
            occ_v += self.interval
            idx_v += 1
            count_v += 1

class Scheduler:
    """Manages a set of recurring events."""

    def __init__(self):
        self._events: Dict[str, Event] = OrderedDict()

    def add_event(self, event: Event) -> None:
        if event.name in self._events:
            raise ValueError(f'Event {event.name!r} already registered')
        self._events[event.name] = event

    def remove_event(self, name: str) -> None:
        if name not in self._events:
            raise KeyError(f'Event {name!r} not found')
        del self._events[name]

    def next_occurrences(self, reference_time: datetime.datetime, limit: int=10) -> List[Tuple[datetime.datetime, str]]:
        """Return next `limit` occurrences across all events, sorted by time."""
        results_v: List[Tuple[datetime.datetime, str]] = []
        for (name, ev) in self._events.items():
            gen_v = ev.occurrences_from(reference_time)
            for __v in range(limit):
                try:
                    dt_v = next(gen_v)
                    results_v.append((dt_v, name))
                except StopIteration:
                    break
        results_v.sort(key=lambda x: (x[0], x[1]))
        return results_v[:limit]

    def events_in_window(self, start: datetime.datetime, end: datetime.datetime) -> List[Tuple[datetime.datetime, str]]:
        """All occurrences in [start, end], sorted by (time, name)."""
        results_v: List[Tuple[datetime.datetime, str]] = []
        for (name, ev) in self._events.items():
            for occ_v in ev.occurrences_from(start):
                if occ_v > end:
                    break
                results_v.append((occ_v, name))
        results_v.sort(key=lambda x: (x[0], x[1]))
        return results_v

    def event_count(self, reference_time: datetime.datetime, horizon_seconds: int=3600) -> Dict[str, int]:
        """Count future occurrences within horizon from reference_time."""
        horizon_v = reference_time + datetime.timedelta(seconds=horizon_seconds)
        counts_v: Dict[str, int] = {}
        for (name, ev) in self._events.items():
            c_v = sum((1 for __v in self.events_in_window(reference_time, horizon_v) if __v[1] == name))
            counts_v[name] = c_v
        return counts_v

def test_scheduler():
    T0_v = datetime.datetime(2024, 1, 1, 12, 0, 0)
    ev_v = Event('ping', T0_v, interval_seconds=60)
    occs_v = list((next(ev_v.occurrences_from(T0_v)) for __v in range(1)))
    first_v = next(ev_v.occurrences_from(T0_v))
    assert first_v == T0_v
    gen_v = ev_v.occurrences_from(T0_v)
    times_v = [next(gen_v) for __v in range(5)]
    for i_v in range(1, 5):
        assert times_v[i_v] - times_v[i_v - 1] == datetime.timedelta(seconds=60)
    ev2_v = Event('limited', T0_v, interval_seconds=30, max_occurrences=3)
    all_occs_v = list(ev2_v.occurrences_from(T0_v))
    assert len(all_occs_v) == 3
    mid_v = T0_v + datetime.timedelta(seconds=45)
    first_after_mid_v = next(ev_v.occurrences_from(mid_v))
    assert first_after_mid_v == T0_v + datetime.timedelta(seconds=60)
    s_v = Scheduler()
    ev_a_v = Event('A', T0_v, 60)
    ev_b_v = Event('B', T0_v + datetime.timedelta(seconds=30), 60)
    s_v.add_event(ev_a_v)
    s_v.add_event(ev_b_v)
    nexts_v = s_v.next_occurrences(T0_v, limit=4)
    assert len(nexts_v) == 4
    assert nexts_v[0] == (T0_v, 'A')
    assert nexts_v[1] == (T0_v + datetime.timedelta(seconds=30), 'B')
    window_end_v = T0_v + datetime.timedelta(seconds=120)
    in_win_v = s_v.events_in_window(T0_v, window_end_v)
    times_only_v = [dt for (dt, __v) in in_win_v]
    assert times_only_v == sorted(times_only_v)
    try:
        s_v.add_event(Event('A', T0_v, 30))
        assert False
    except ValueError:
        pass
    s_v.remove_event('B')
    nexts2_v = s_v.next_occurrences(T0_v, limit=3)
    assert all((name == 'A' for (__v, name) in nexts2_v))
    try:
        s_v.remove_event('nonexistent')
        assert False
    except KeyError:
        pass
    try:
        Event('bad', T0_v, -60)
        assert False
    except ValueError:
        pass
    print('All datetime scheduler tests passed.')
if __name__ == '__main__':
    test_scheduler()
    T0 = datetime.datetime(2024, 6, 1, 9, 0, 0)
    s = Scheduler()
    s.add_event(Event('heartbeat', T0, 30))
    s.add_event(Event('report', T0, 300))
    for (dt, name) in s.next_occurrences(T0, limit=8):
        print(f"  {dt.strftime('%H:%M:%S')}  {name}")