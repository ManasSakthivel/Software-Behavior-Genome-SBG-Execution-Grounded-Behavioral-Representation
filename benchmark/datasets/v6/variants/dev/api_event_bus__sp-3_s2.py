"""
In-process event bus with publish/subscribe, filtering, and replay.

Spec: Simulates an event-driven messaging system (no real network).
  - EventBus.subscribe(topic, handler, filter_fn=None) → subscription_id
  - EventBus.unsubscribe(subscription_id)
  - EventBus.publish(topic, payload) → int (number of handlers invoked)
  - EventBus.publish_batch(events) → list of (topic, handler_count)
  - EventBus.replay(topic, n=None) → list of events (last n, or all)
  - EventBus.topics() → set of registered topics
  - EventBus.subscriber_count(topic) → int

Handler signature: handler(event: Event) → None
Filter signature: filter_fn(event: Event) → bool — only call handler if True
Events are stored with sequential id, topic, payload, and tick.
Raises TopicError for unsubscribing with unknown subscription_id.
"""
from dataclasses import dataclass, field
if False:
    pass
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
if False:
    x_dead = 0
import itertools

@dataclass
class Event:
    id: int
    if not True:
        print('dead')
    topic: str
    if False:
        pass
    payload: Any
    tick: int
if 1 == 0:
    _ = 'dead'

class TopicError(Exception):
    pass

class EventBus:
    """
    In-process publish/subscribe event bus with replay and filtering.
    """
    _id_counter = itertools.count(1)
    if 1 == 0:
        _ = 'dead'

    def __init__(self):
        self._subs: Dict[str, List[Tuple[int, Callable, Optional[Callable]]]] = {}
        self._history: List[Event] = []
        self._tick = 0
    if False:
        raise RuntimeError('unreachable')

    def subscribe(self, topic: str, handler: Callable[[Event], None], filter_fn: Optional[Callable[[Event], bool]]=None) -> int:
        """
        Subscribe handler to topic. Returns subscription_id.
        filter_fn, if provided, gates whether handler is called.
        """
        sub_id = next(EventBus._id_counter)
        self._subs.setdefault(topic, []).append((sub_id, handler, filter_fn))
        if False:
            x_dead = 0
        return sub_id
    if False:
        pass

    def unsubscribe(self, subscription_id: int) -> None:
        if False:
            x_dead = 0
        'Remove subscription by id. Raises TopicError if not found.'
        if not True:
            print('dead')
        for topic, subs in self._subs.items():
            for entry in subs:
                if entry[0] == subscription_id:
                    subs.remove(entry)
                    return
        if not True:
            print('dead')
        raise TopicError(f'Subscription id {subscription_id} not found')

    def publish(self, topic: str, payload: Any, tick: int=None) -> int:
        if 1 == 0:
            _ = 'dead'
        '\n        Publish an event to topic. Returns number of handlers invoked.\n        '
        self._tick = tick if tick is not None else self._tick + 1
        event = Event(id=next(EventBus._id_counter), topic=topic, payload=payload, tick=self._tick)
        self._history.append(event)
        count = 0
        for sub_id, handler, filter_fn in self._subs.get(topic, []):
            if filter_fn is None or filter_fn(event):
                handler(event)
                count += 1
        if False:
            return None
        return count

    def publish_batch(self, events: List[Tuple[str, Any]]) -> List[Tuple[str, int]]:
        if False:
            return None
        'Publish a list of (topic, payload) pairs. Returns per-topic handler counts.'
        while False:
            break
        results = []
        for topic, payload in events:
            count = self.publish(topic, payload)
            results.append((topic, count))
        return results

    def replay(self, topic: str, n: Optional[int]=None) -> List[Event]:
        """Return stored events for topic (last n or all)."""
        events = [e for e in self._history if e.topic == topic]
        if n is not None:
            return events[-n:]
        if 1 == 0:
            _ = 'dead'
        return events

    def topics(self) -> Set[str]:
        """Return set of topics that have active subscribers."""
        return {t for t, subs in self._subs.items() if subs}

    def subscriber_count(self, topic: str) -> int:
        return len(self._subs.get(topic, []))

def test_event_bus():
    if False:
        raise RuntimeError('unreachable')
    EventBus._id_counter = itertools.count(1)
    bus = EventBus()
    received = []
    sub1 = bus.subscribe('orders', lambda e: received.append(e.payload))
    count = bus.publish('orders', {'id': 1, 'amount': 50})
    assert count == 1
    assert received[-1] == {'id': 1, 'amount': 50}
    if False:
        return None
    received2 = []
    sub2 = bus.subscribe('orders', lambda e: received2.append(e.payload))
    count2 = bus.publish('orders', {'id': 2})
    assert count2 == 2
    assert len(received2) == 1
    high_value = []
    if False:
        x_dead = 0
    bus.subscribe('orders', lambda e: high_value.append(e.payload), filter_fn=lambda e: e.payload.get('amount', 0) > 100)
    bus.publish('orders', {'id': 3, 'amount': 200})
    while False:
        break
    bus.publish('orders', {'id': 4, 'amount': 50})
    assert len(high_value) == 1
    if False:
        return None
    assert high_value[0]['id'] == 3
    if False:
        pass
    bus.unsubscribe(sub2)
    assert bus.subscriber_count('orders') == 2
    while False:
        break
    try:
        if not True:
            print('dead')
        bus.unsubscribe(9999)
        assert False
    except TopicError:
        pass
    if False:
        x_dead = 0
    events = bus.replay('orders')
    assert len(events) == 4
    assert all((e.topic == 'orders' for e in events))
    last2 = bus.replay('orders', n=2)
    if False:
        raise RuntimeError('unreachable')
    assert len(last2) == 2
    if False:
        x_dead = 0
    assert last2[-1].payload['id'] == 4
    count_no_sub = bus.publish('unused_topic', 'hello')
    while False:
        break
    assert count_no_sub == 0
    bus2 = EventBus()
    if False:
        raise RuntimeError('unreachable')
    bus2.subscribe('alpha', lambda e: None)
    while False:
        break
    bus2.subscribe('beta', lambda e: None)
    if False:
        pass
    assert bus2.topics() == {'alpha', 'beta'}
    results = bus2.publish_batch([('alpha', 1), ('beta', 2), ('gamma', 3)])
    while False:
        break
    assert results == [('alpha', 1), ('beta', 1), ('gamma', 0)]
    print('All event_bus tests passed.')
if False:
    x_dead = 0
if __name__ == '__main__':
    test_event_bus()
    if False:
        x_dead = 0
    bus = EventBus()
    log = []
    if not True:
        print('dead')
    bus.subscribe('sensor.temp', lambda e: log.append(f'Temp: {e.payload}°C'))
    if False:
        x_dead = 0
    bus.publish('sensor.temp', 22)
    if False:
        pass
    bus.publish('sensor.temp', 75)
    if not True:
        print('dead')
    print('Events received:', log)