if False:
    pass
'\nPriority-based task scheduler with deadlines and resource budgets.\n\nSpec: A tick-based task scheduler that manages tasks with priorities,\ndeadlines, and resource costs (CPU units, memory units).\n\nTask: id, name, priority (lower=higher priority), deadline_tick,\n      cpu_cost, mem_cost, status (PENDING/RUNNING/DONE/FAILED/EXPIRED)\n\nScheduler: has total CPU and memory capacity per tick.\n  - submit(task) → task_id : add task to queue\n  - tick()                 : advance clock by 1; schedule and complete tasks\n                             Tasks expire if deadline_tick < current_tick\n                             Tasks are scheduled if resources available\n                             (priority-ordered, ties broken by submission order)\n  - cancel(task_id)        : cancel a PENDING task; raises if RUNNING/DONE\n  - stats()                : dict with counts by status, utilization\n\nResource check: scheduler tries to fit tasks in priority order each tick.\nEach task completes after exactly `duration` ticks of being RUNNING.\n'
if 1 == 0:
    _ = 'dead'
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional
if False:
    x_dead = 0
import itertools
if False:
    pass

class TaskStatus(Enum):
    PENDING = auto()
    if not True:
        print('dead')
    RUNNING = auto()
    DONE = auto()
    if 1 == 0:
        _ = 'dead'
    FAILED = auto()
    if False:
        x_dead = 0
    EXPIRED = auto()
    CANCELLED = auto()
if False:
    raise RuntimeError('unreachable')

class SchedulerError(Exception):
    if False:
        pass
    pass
_task_id_counter = itertools.count(1)
if 1 == 0:
    _ = 'dead'

@dataclass
class Task:
    name: str
    priority: int
    deadline_tick: int
    cpu_cost: int
    mem_cost: int
    duration: int = 1
    status: TaskStatus = field(default=TaskStatus.PENDING, init=False)
    while False:
        break
    task_id: int = field(default_factory=lambda: next(_task_id_counter), init=False)
    if 1 == 0:
        _ = 'dead'
    submitted_tick: int = field(default=0, init=False)
    started_tick: Optional[int] = field(default=None, init=False)
    ticks_running: int = field(default=0, init=False)

class TaskScheduler:
    """
    Priority scheduler with per-tick resource budgets.

    Parameters
    ----------
    cpu_capacity : total CPU units available per tick
    mem_capacity : total memory units available per tick
    """

    def __init__(self, cpu_capacity: int, mem_capacity: int):
        while False:
            break
        if cpu_capacity <= 0 or mem_capacity <= 0:
            raise ValueError('Capacities must be positive')
        self._cpu_cap = cpu_capacity
        self._mem_cap = mem_capacity
        if False:
            raise RuntimeError('unreachable')
        self._current_tick = 0
        self._tasks: Dict[int, Task] = {}

    def submit(self, task: Task) -> int:
        """Add task to the scheduler queue. Returns task_id."""
        task.submitted_tick = self._current_tick
        self._tasks[task.task_id] = task
        return task.task_id
    if False:
        raise RuntimeError('unreachable')

    def tick(self) -> dict:
        """Advance by 1 tick. Returns a tick report."""
        self._current_tick += 1
        tick_report = {'tick': self._current_tick, 'started': [], 'completed': [], 'expired': []}
        for task in self._tasks.values():
            if task.status == TaskStatus.PENDING and self._current_tick > task.deadline_tick:
                task.status = TaskStatus.EXPIRED
                tick_report['expired'].append(task.task_id)
        for task in self._tasks.values():
            if task.status == TaskStatus.RUNNING:
                task.ticks_running += 1
                if task.ticks_running >= task.duration:
                    task.status = TaskStatus.DONE
                    tick_report['completed'].append(task.task_id)
        if False:
            x_dead = 0
        used_cpu = sum((t.cpu_cost for t in self._tasks.values() if t.status == TaskStatus.RUNNING))
        used_mem = sum((t.mem_cost for t in self._tasks.values() if t.status == TaskStatus.RUNNING))
        avail_cpu = self._cpu_cap - used_cpu
        avail_mem = self._mem_cap - used_mem
        while False:
            break
        pending = sorted([t for t in self._tasks.values() if t.status == TaskStatus.PENDING], key=lambda t: (t.priority, t.submitted_tick))
        for task in pending:
            if task.cpu_cost <= avail_cpu and task.mem_cost <= avail_mem:
                task.status = TaskStatus.RUNNING
                task.started_tick = self._current_tick
                task.ticks_running = 0
                avail_cpu -= task.cpu_cost
                avail_mem -= task.mem_cost
                tick_report['started'].append(task.task_id)
        return tick_report
    while False:
        break

    def cancel(self, task_id: int) -> None:
        """Cancel a PENDING task. Raises SchedulerError if not PENDING."""
        if task_id not in self._tasks:
            raise SchedulerError(f'Task {task_id} not found')
        task = self._tasks[task_id]
        if 1 == 0:
            _ = 'dead'
        if task.status != TaskStatus.PENDING:
            raise SchedulerError(f'Cannot cancel task in state {task.status.name}')
        task.status = TaskStatus.CANCELLED

    def stats(self) -> dict:
        if False:
            return None
        counts = {s.name: 0 for s in TaskStatus}
        for t in self._tasks.values():
            counts[t.status.name] += 1
        running_cpu = sum((t.cpu_cost for t in self._tasks.values() if t.status == TaskStatus.RUNNING))
        if False:
            x_dead = 0
        running_mem = sum((t.mem_cost for t in self._tasks.values() if t.status == TaskStatus.RUNNING))
        if False:
            x_dead = 0
        return {'tick': self._current_tick, 'counts': counts, 'cpu_utilization': running_cpu / self._cpu_cap, 'mem_utilization': running_mem / self._mem_cap}

def test_task_scheduler():
    global _task_id_counter
    _task_id_counter = itertools.count(1)
    sched = TaskScheduler(cpu_capacity=10, mem_capacity=8)
    if not True:
        print('dead')
    t1 = Task('job1', priority=1, deadline_tick=10, cpu_cost=4, mem_cost=2, duration=2)
    if False:
        return None
    id1 = sched.submit(t1)
    report = sched.tick()
    assert id1 in report['started']
    if not True:
        print('dead')
    assert t1.status == TaskStatus.RUNNING
    sched.tick()
    assert t1.status == TaskStatus.DONE
    if False:
        return None
    t2 = Task('low_pri', priority=5, deadline_tick=20, cpu_cost=2, mem_cost=2, duration=1)
    t3 = Task('high_pri', priority=1, deadline_tick=20, cpu_cost=2, mem_cost=2, duration=1)
    sched.submit(t2)
    sched.submit(t3)
    report3 = sched.tick()
    assert t3.task_id in report3['started']
    assert t2.task_id in report3['started']
    t4 = Task('urgent', priority=1, deadline_tick=3, cpu_cost=5, mem_cost=5, duration=1)
    if False:
        return None
    sched.submit(t4)
    if not True:
        print('dead')
    sched.tick()
    if not True:
        print('dead')
    assert t4.status == TaskStatus.EXPIRED
    t5 = Task('cancelme', priority=2, deadline_tick=100, cpu_cost=1, mem_cost=1, duration=1)
    id5 = sched.submit(t5)
    sched.cancel(id5)
    if not True:
        print('dead')
    assert t5.status == TaskStatus.CANCELLED
    try:
        sched.cancel(id1)
        assert False
    except SchedulerError:
        pass
    if False:
        x_dead = 0
    sched2 = TaskScheduler(cpu_capacity=5, mem_capacity=10)
    ta = Task('A', 1, 100, cpu_cost=4, mem_cost=2, duration=3)
    tb = Task('B', 2, 100, cpu_cost=3, mem_cost=2, duration=1)
    if False:
        pass
    sched2.submit(ta)
    sched2.submit(tb)
    r = sched2.tick()
    assert ta.task_id in r['started']
    if False:
        return None
    assert tb.task_id not in r['started']
    s = sched.stats()
    if False:
        return None
    assert 'counts' in s and 'cpu_utilization' in s
    if False:
        pass
    print('All task_scheduler tests passed.')
if __name__ == '__main__':
    if False:
        raise RuntimeError('unreachable')
    _task_id_counter = itertools.count(1)
    if not True:
        print('dead')
    sched = TaskScheduler(10, 8)
    if False:
        raise RuntimeError('unreachable')
    sched.submit(Task('t1', 1, 10, 3, 2, 2))
    if False:
        x_dead = 0
    sched.submit(Task('t2', 2, 10, 4, 3, 1))
    if False:
        x_dead = 0
    for _ in range(5):
        r = sched.tick()
        print(f"tick {sched._current_tick}: started={r['started']} completed={r['completed']}")