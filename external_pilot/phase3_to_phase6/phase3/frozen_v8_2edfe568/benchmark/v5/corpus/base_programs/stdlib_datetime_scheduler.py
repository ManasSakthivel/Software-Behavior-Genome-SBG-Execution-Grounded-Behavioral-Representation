# program_id: stdlib_datetime_scheduler
# category: stdlib_interactions
# spec_version: 1.0

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

    def __init__(self, name: str, start: datetime.datetime,
                 interval_seconds: int, max_occurrences: Optional[int] = None):
        if interval_seconds <= 0:
            raise ValueError(f"interval_seconds must be > 0, got {interval_seconds}")
        if max_occurrences is not None and max_occurrences < 1:
            raise ValueError(f"max_occurrences must be >= 1 or None")
        self.name = name
        self.start = start
        self.interval = datetime.timedelta(seconds=interval_seconds)
        self.max_occurrences = max_occurrences

    def occurrences_from(self, ref: datetime.datetime) -> Iterator[datetime.datetime]:
        """Yield all occurrences at or after `ref`, up to max_occurrences."""
        count = 0
        # Find the first occurrence >= ref
        if ref <= self.start:
            occ = self.start
            idx = 0
        else:
            delta = ref - self.start
            steps = int(delta / self.interval)
            occ = self.start + self.interval * steps
            if occ < ref:
                occ += self.interval
                steps += 1
            idx = steps

        while True:
            if self.max_occurrences is not None and idx >= self.max_occurrences:
                break
            yield occ
            occ += self.interval
            idx += 1
            count += 1


class Scheduler:
    """Manages a set of recurring events."""

    def __init__(self):
        self._events: Dict[str, Event] = OrderedDict()

    def add_event(self, event: Event) -> None:
        if event.name in self._events:
            raise ValueError(f"Event {event.name!r} already registered")
        self._events[event.name] = event

    def remove_event(self, name: str) -> None:
        if name not in self._events:
            raise KeyError(f"Event {name!r} not found")
        del self._events[name]

    def next_occurrences(
        self, reference_time: datetime.datetime, limit: int = 10
    ) -> List[Tuple[datetime.datetime, str]]:
        """Return next `limit` occurrences across all events, sorted by time."""
        results: List[Tuple[datetime.datetime, str]] = []
        for name, ev in self._events.items():
            gen = ev.occurrences_from(reference_time)
            for _ in range(limit):
                try:
                    dt = next(gen)
                    results.append((dt, name))
                except StopIteration:
                    break
        results.sort(key=lambda x: (x[0], x[1]))
        return results[:limit]

    def events_in_window(
        self, start: datetime.datetime, end: datetime.datetime
    ) -> List[Tuple[datetime.datetime, str]]:
        """All occurrences in [start, end], sorted by (time, name)."""
        results: List[Tuple[datetime.datetime, str]] = []
        for name, ev in self._events.items():
            for occ in ev.occurrences_from(start):
                if occ > end:
                    break
                results.append((occ, name))
        results.sort(key=lambda x: (x[0], x[1]))
        return results

    def event_count(
        self, reference_time: datetime.datetime, horizon_seconds: int = 3600
    ) -> Dict[str, int]:
        """Count future occurrences within horizon from reference_time."""
        horizon = reference_time + datetime.timedelta(seconds=horizon_seconds)
        counts: Dict[str, int] = {}
        for name, ev in self._events.items():
            c = sum(1 for _ in self.events_in_window(reference_time, horizon)
                    if _ [1] == name)
            counts[name] = c
        return counts


# ---------- tests ----------

def test_scheduler():
    T0 = datetime.datetime(2024, 1, 1, 12, 0, 0)

    # Test 1: basic occurrence generation
    ev = Event("ping", T0, interval_seconds=60)
    occs = list(next(ev.occurrences_from(T0)) for _ in range(1))
    first = next(ev.occurrences_from(T0))
    assert first == T0

    # Test 2: occurrences step by interval
    gen = ev.occurrences_from(T0)
    times = [next(gen) for _ in range(5)]
    for i in range(1, 5):
        assert times[i] - times[i-1] == datetime.timedelta(seconds=60)

    # Test 3: max_occurrences respected
    ev2 = Event("limited", T0, interval_seconds=30, max_occurrences=3)
    all_occs = list(ev2.occurrences_from(T0))
    assert len(all_occs) == 3

    # Test 4: occurrences_from mid-interval picks up next occurrence
    mid = T0 + datetime.timedelta(seconds=45)  # between T0 and T0+60s
    first_after_mid = next(ev.occurrences_from(mid))
    assert first_after_mid == T0 + datetime.timedelta(seconds=60)

    # Test 5: Scheduler add / next_occurrences
    s = Scheduler()
    ev_a = Event("A", T0, 60)
    ev_b = Event("B", T0 + datetime.timedelta(seconds=30), 60)
    s.add_event(ev_a)
    s.add_event(ev_b)
    nexts = s.next_occurrences(T0, limit=4)
    assert len(nexts) == 4
    assert nexts[0] == (T0, "A")
    assert nexts[1] == (T0 + datetime.timedelta(seconds=30), "B")

    # Test 6: events_in_window
    window_end = T0 + datetime.timedelta(seconds=120)
    in_win = s.events_in_window(T0, window_end)
    times_only = [dt for dt, _ in in_win]
    assert times_only == sorted(times_only)  # sorted

    # Test 7: duplicate event name raises ValueError
    try:
        s.add_event(Event("A", T0, 30))
        assert False
    except ValueError:
        pass

    # Test 8: remove_event
    s.remove_event("B")
    nexts2 = s.next_occurrences(T0, limit=3)
    assert all(name == "A" for _, name in nexts2)

    # Test 9: remove missing event raises KeyError
    try:
        s.remove_event("nonexistent")
        assert False
    except KeyError:
        pass

    # Test 10: negative interval raises ValueError
    try:
        Event("bad", T0, -60)
        assert False
    except ValueError:
        pass

    print("All datetime scheduler tests passed.")


if __name__ == "__main__":
    test_scheduler()
    T0 = datetime.datetime(2024, 6, 1, 9, 0, 0)
    s = Scheduler()
    s.add_event(Event("heartbeat", T0, 30))
    s.add_event(Event("report", T0, 300))
    for dt, name in s.next_occurrences(T0, limit=8):
        print(f"  {dt.strftime('%H:%M:%S')}  {name}")
