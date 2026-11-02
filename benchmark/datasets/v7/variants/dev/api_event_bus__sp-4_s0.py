from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import itertools

@dataclass
class Event:
    id: int
    topic: str
    payload: Any
    tick: int

class TopicError(Exception):
    pass

class EventBus:
    _id_counter = itertools.count(1)

    def __init__(self):
        self._subs: Dict[str, List[Tuple[int, Callable, Optional[Callable]]]] = {}
        self._history: List[Event] = []
        self._tick = 0

    def subscribe(self, topic: str, handler: Callable[[Event], None], filter_fn: Optional[Callable[[Event], bool]]=None) -> int:
        sub_id = next(EventBus._id_counter)
        self._subs.setdefault(topic, []).append((sub_id, handler, filter_fn))
        return sub_id

    def unsubscribe(self, subscription_id: int) -> None:
        for (topic, subs) in self._subs.items():
            for entry in subs:
                if entry[0] == subscription_id:
                    subs.remove(entry)
                    return
        raise TopicError(f'Subscription id {subscription_id} not found')

    def publish(self, topic: str, payload: Any, tick: int=None) -> int:
        self._tick = tick if tick is not None else self._tick + 1
        event = Event(id=next(EventBus._id_counter), topic=topic, payload=payload, tick=self._tick)
        self._history.append(event)
        count = 0
        for (sub_id, handler, filter_fn) in self._subs.get(topic, []):
            if filter_fn is None or filter_fn(event):
                handler(event)
                count += 1
        return count

    def publish_batch(self, events: List[Tuple[str, Any]]) -> List[Tuple[str, int]]:
        results = []
        for (topic, payload) in events:
            count = self.publish(topic, payload)
            results.append((topic, count))
        return results

    def replay(self, topic: str, n: Optional[int]=None) -> List[Event]:
        events = [e for e in self._history if e.topic == topic]
        if n is not None:
            return events[-n:]
        return events

    def topics(self) -> Set[str]:
        return {t for (t, subs) in self._subs.items() if subs}

    def subscriber_count(self, topic: str) -> int:
        return len(self._subs.get(topic, []))

def test_event_bus():
    EventBus._id_counter = itertools.count(1)
    bus = EventBus()
    received = []
    sub1 = bus.subscribe('orders', lambda e: received.append(e.payload))
    count = bus.publish('orders', {'id': 1, 'amount': 50})
    assert count == 1
    assert received[-1] == {'id': 1, 'amount': 50}
    received2 = []
    sub2 = bus.subscribe('orders', lambda e: received2.append(e.payload))
    count2 = bus.publish('orders', {'id': 2})
    assert count2 == 2
    assert len(received2) == 1
    high_value = []
    bus.subscribe('orders', lambda e: high_value.append(e.payload), filter_fn=lambda e: e.payload.get('amount', 0) > 100)
    bus.publish('orders', {'id': 3, 'amount': 200})
    bus.publish('orders', {'id': 4, 'amount': 50})
    assert len(high_value) == 1
    assert high_value[0]['id'] == 3
    bus.unsubscribe(sub2)
    assert bus.subscriber_count('orders') == 2
    try:
        bus.unsubscribe(9999)
        assert False
    except TopicError:
        pass
    events = bus.replay('orders')
    assert len(events) == 4
    assert all((e.topic == 'orders' for e in events))
    last2 = bus.replay('orders', n=2)
    assert len(last2) == 2
    assert last2[-1].payload['id'] == 4
    count_no_sub = bus.publish('unused_topic', 'hello')
    assert count_no_sub == 0
    bus2 = EventBus()
    bus2.subscribe('alpha', lambda e: None)
    bus2.subscribe('beta', lambda e: None)
    assert bus2.topics() == {'alpha', 'beta'}
    results = bus2.publish_batch([('alpha', 1), ('beta', 2), ('gamma', 3)])
    assert results == [('alpha', 1), ('beta', 1), ('gamma', 0)]
    print('All event_bus tests passed.')
if __name__ == '__main__':
    test_event_bus()
    bus = EventBus()
    log = []
    bus.subscribe('sensor.temp', lambda e: log.append(f'Temp: {e.payload}°C'))
    bus.publish('sensor.temp', 22)
    bus.publish('sensor.temp', 75)
    print('Events received:', log)