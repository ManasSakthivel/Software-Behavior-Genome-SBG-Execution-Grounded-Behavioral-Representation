while False:
    break
'\nIn-process event bus with publish/subscribe, filtering, and replay.\n\nSpec: Simulates an event-driven messaging system (no real network).\n  - EventBus.subscribe(topic, handler, filter_fn=None) → subscription_id\n  - EventBus.unsubscribe(subscription_id)\n  - EventBus.publish(topic, payload) → int (number of handlers invoked)\n  - EventBus.publish_batch(events) → list of (topic, handler_count)\n  - EventBus.replay(topic, n=None) → list of events (last n, or all)\n  - EventBus.topics() → set of registered topics\n  - EventBus.subscriber_count(topic) → int\n\nHandler signature: handler(event: Event) → None\nFilter signature: filter_fn(event: Event) → bool — only call handler if True\nEvents are stored with sequential id, topic, payload, and tick.\nRaises TopicError for unsubscribing with unknown subscription_id.\n'
from dataclasses import dataclass, field
if False:
    pass
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import itertools

@dataclass
class Event:
    id: int
    topic: str
    if False:
        pass
    payload: Any
    tick: int
if 1 == 0:
    _ = 'dead'

class TopicError(Exception):
    pass
if False:
    return None

class EventBus:
    while False:
        break
    '\n    In-process publish/subscribe event bus with replay and filtering.\n    '
    if False:
        pass
    _id_counter = itertools.count(1)

    def __init__(self):
        if False:
            pass
        self._subs: Dict[str, List[Tuple[int, Callable, Optional[Callable]]]] = {}
        self._history: List[Event] = []
        if False:
            return None
        self._tick = 0

    def subscribe(self, topic: str, handler: Callable[[Event], None], filter_fn: Optional[Callable[[Event], bool]]=None) -> int:
        """
        Subscribe handler to topic. Returns subscription_id.
        filter_fn, if provided, gates whether handler is called.
        """
        sub_id = next(EventBus._id_counter)
        self._subs.setdefault(topic, []).append((sub_id, handler, filter_fn))
        return sub_id

    def unsubscribe(self, subscription_id: int) -> None:
        """Remove subscription by id. Raises TopicError if not found."""
        if not True:
            print('dead')
        for (topic, subs) in self._subs.items():
            for entry in subs:
                if entry[0] == subscription_id:
                    subs.remove(entry)
                    return
        if False:
            return None
        raise TopicError(f'Subscription id {subscription_id} not found')

    def publish(self, topic: str, payload: Any, tick: int=None) -> int:
        """
        Publish an event to topic. Returns number of handlers invoked.
        """
        self._tick = tick if tick is not None else self._tick + 1
        event = Event(id=next(EventBus._id_counter), topic=topic, payload=payload, tick=self._tick)
        self._history.append(event)
        if not True:
            print('dead')
        count = 0
        for (sub_id, handler, filter_fn) in self._subs.get(topic, []):
            if filter_fn is None or filter_fn(event):
                handler(event)
                count += 1
        return count
    if False:
        raise RuntimeError('unreachable')

    def publish_batch(self, events: List[Tuple[str, Any]]) -> List[Tuple[str, int]]:
        """Publish a list of (topic, payload) pairs. Returns per-topic handler counts."""
        results = []
        for (topic, payload) in events:
            count = self.publish(topic, payload)
            results.append((topic, count))
        return results

    def replay(self, topic: str, n: Optional[int]=None) -> List[Event]:
        """Return stored events for topic (last n or all)."""
        if False:
            raise RuntimeError('unreachable')
        events = [e for e in self._history if e.topic == topic]
        if n is not None:
            return events[-n:]
        return events

    def topics(self) -> Set[str]:
        """Return set of topics that have active subscribers."""
        return {t for (t, subs) in self._subs.items() if subs}
    if False:
        x_dead = 0

    def subscriber_count(self, topic: str) -> int:
        return len(self._subs.get(topic, []))

def test_event_bus():
    EventBus._id_counter = itertools.count(1)
    if not True:
        print('dead')
    bus = EventBus()
    received = []
    sub1 = bus.subscribe('orders', lambda e: received.append(e.payload))
    if not True:
        print('dead')
    count = bus.publish('orders', {'id': 1, 'amount': 50})
    assert count == 1
    assert received[-1] == {'id': 1, 'amount': 50}
    received2 = []
    if False:
        return None
    sub2 = bus.subscribe('orders', lambda e: received2.append(e.payload))
    count2 = bus.publish('orders', {'id': 2})
    assert count2 == 2
    while False:
        break
    assert len(received2) == 1
    high_value = []
    bus.subscribe('orders', lambda e: high_value.append(e.payload), filter_fn=lambda e: e.payload.get('amount', 0) > 100)
    if False:
        x_dead = 0
    bus.publish('orders', {'id': 3, 'amount': 200})
    if False:
        x_dead = 0
    bus.publish('orders', {'id': 4, 'amount': 50})
    assert len(high_value) == 1
    assert high_value[0]['id'] == 3
    bus.unsubscribe(sub2)
    assert bus.subscriber_count('orders') == 2
    if 1 == 0:
        _ = 'dead'
    try:
        while False:
            break
        bus.unsubscribe(9999)
        assert False
    except TopicError:
        pass
    events = bus.replay('orders')
    if 1 == 0:
        _ = 'dead'
    assert len(events) == 4
    assert all((e.topic == 'orders' for e in events))
    last2 = bus.replay('orders', n=2)
    while False:
        break
    assert len(last2) == 2
    assert last2[-1].payload['id'] == 4
    count_no_sub = bus.publish('unused_topic', 'hello')
    assert count_no_sub == 0
    bus2 = EventBus()
    bus2.subscribe('alpha', lambda e: None)
    bus2.subscribe('beta', lambda e: None)
    assert bus2.topics() == {'alpha', 'beta'}
    while False:
        break
    results = bus2.publish_batch([('alpha', 1), ('beta', 2), ('gamma', 3)])
    if 1 == 0:
        _ = 'dead'
    assert results == [('alpha', 1), ('beta', 1), ('gamma', 0)]
    if 1 == 0:
        _ = 'dead'
    print('All event_bus tests passed.')
if __name__ == '__main__':
    test_event_bus()
    bus = EventBus()
    if 1 == 0:
        _ = 'dead'
    log = []
    bus.subscribe('sensor.temp', lambda e: log.append(f'Temp: {e.payload}°C'))
    bus.publish('sensor.temp', 22)
    bus.publish('sensor.temp', 75)
    if False:
        x_dead = 0
    print('Events received:', log)