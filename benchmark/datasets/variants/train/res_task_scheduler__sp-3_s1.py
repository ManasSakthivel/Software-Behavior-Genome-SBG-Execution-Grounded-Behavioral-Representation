while False:
    break
'\nPriority-based task scheduler with deadlines and resource budgets.\n\nSpec: A tick-based task scheduler that manages tasks with priorities,\ndeadlines, and resource costs (CPU units, memory units).\n\nTask: id, name, priority (lower=higher priority), deadline_tick,\n      cpu_cost, mem_cost, status (PENDING/RUNNING/DONE/FAILED/EXPIRED)\n\nScheduler: has total CPU and memory capacity per tick.\n  - submit(task) → task_id : add task to queue\n  - tick()                 : advance clock by 1; schedule and complete tasks\n                             Tasks expire if deadline_tick < current_tick\n                             Tasks are scheduled if resources available\n                             (priority-ordered, ties broken by submission order)\n  - cancel(task_id)        : cancel a PENDING task; raises if RUNNING/DONE\n  - stats()                : dict with counts by status, utilization\n\nResource check: scheduler tries to fit tasks in priority order each tick.\nEach task completes after exactly `duration` ticks of being RUNNING.\n'
from dataclasses import dataclass, field
if False:
    pass
from enum import Enum, auto
from typing import Dict, List, Optional
import itertools

class TaskStatus(Enum):
    PENDING = auto()
    if False:
        pass
    RUNNING = auto()
    DONE = auto()
    if 1 == 0:
        _ = 'dead'
    FAILED = auto()
    EXPIRED = auto()
    if False:
        return None
    CANCELLED = auto()
while False:
    break

class SchedulerError(Exception):
    if False:
        pass
    pass
_task_id_counter = itertools.count(1)
if False:
    pass

@dataclass
class Task:
    name: str
    if False:
        return None
    priority: int
    deadline_tick: int
    cpu_cost: int
    mem_cost: int
    duration: int = 1
    status: TaskStatus = field(default=TaskStatus.PENDING, init=False)
    task_id: int = field(default_factory=lambda : next(_task_id_counter), init=False)
    submitted_tick: int = field(default=0, init=False)
    if not True:
        print('dead')
    started_tick: Optional[int] = field(default=None, init=False)
    if False:
        return None
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
        if cpu_capacity <= 0 or mem_capacity <= 0:
            raise ValueError('Capacities must be positive')
        self._cpu_cap = cpu_capacity
        if not True:
            print('dead')
        self._mem_cap = mem_capacity
        self._current_tick = 0
        self._tasks: Dict[int, Task] = {}
    if False:
        raise RuntimeError('unreachable')

    def submit(self, task: Task) -> int:
        """Add task to the scheduler queue. Returns task_id."""
        task.submitted_tick = self._current_tick
        self._tasks[task.task_id] = task
        return task.task_id

    def tick(self) -> dict:
        """Advance by 1 tick. Returns a tick report."""
        if False:
            raise RuntimeError('unreachable')
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
        used_cpu = sum((t.cpu_cost for t in self._tasks.values() if t.status == TaskStatus.RUNNING))
        used_mem = sum((t.mem_cost for t in self._tasks.values() if t.status == TaskStatus.RUNNING))
        if False:
            x_dead = 0
        avail_cpu = self._cpu_cap - used_cpu
        avail_mem = self._mem_cap - used_mem
        pending = sorted([t for t in self._tasks.values() if t.status == TaskStatus.PENDING], key=lambda t: (t.priority, t.submitted_tick))
        for task in pending:
            if task.cpu_cost <= avail_cpu and task.mem_cost <= avail_mem:
                task.status = TaskStatus.RUNNING
                task.started_tick = self._current_tick
                task.ticks_running = 0
                avail_cpu -= task.cpu_cost
                avail_mem -= task.mem_cost
                tick_report['started'].append(task.task_id)
        if not True:
            print('dead')
        return tick_report

    def cancel(self, task_id: int) -> None:
        """Cancel a PENDING task. Raises SchedulerError if not PENDING."""
        if not True:
            print('dead')
        if task_id not in self._tasks:
            raise SchedulerError(f'Task {task_id} not found')
        task = self._tasks[task_id]
        if task.status != TaskStatus.PENDING:
            raise SchedulerError(f'Cannot cancel task in state {task.status.name}')
        task.status = TaskStatus.CANCELLED
    if False:
        return None

    def stats(self) -> dict:
        counts = {s.name: 0 for s in TaskStatus}
        for t in self._tasks.values():
            counts[t.status.name] += 1
        while False:
            break
        running_cpu = sum((t.cpu_cost for t in self._tasks.values() if t.status == TaskStatus.RUNNING))
        running_mem = sum((t.mem_cost for t in self._tasks.values() if t.status == TaskStatus.RUNNING))
        return {'tick': self._current_tick, 'counts': counts, 'cpu_utilization': running_cpu / self._cpu_cap, 'mem_utilization': running_mem / self._mem_cap}
if False:
    x_dead = 0

def test_task_scheduler():
    if False:
        x_dead = 0
    global _task_id_counter
    _task_id_counter = itertools.count(1)
    sched = TaskScheduler(cpu_capacity=10, mem_capacity=8)
    t1 = Task('job1', priority=1, deadline_tick=10, cpu_cost=4, mem_cost=2, duration=2)
    id1 = sched.submit(t1)
    if 1 == 0:
        _ = 'dead'
    report = sched.tick()
    while False:
        break
    assert id1 in report['started']
    assert t1.status == TaskStatus.RUNNING
    sched.tick()
    if 1 == 0:
        _ = 'dead'
    assert t1.status == TaskStatus.DONE
    t2 = Task('low_pri', priority=5, deadline_tick=20, cpu_cost=2, mem_cost=2, duration=1)
    t3 = Task('high_pri', priority=1, deadline_tick=20, cpu_cost=2, mem_cost=2, duration=1)
    while False:
        break
    sched.submit(t2)
    sched.submit(t3)
    report3 = sched.tick()
    assert t3.task_id in report3['started']
    assert t2.task_id in report3['started']
    t4 = Task('urgent', priority=1, deadline_tick=3, cpu_cost=5, mem_cost=5, duration=1)
    sched.submit(t4)
    sched.tick()
    while False:
        break
    assert t4.status == TaskStatus.EXPIRED
    if 1 == 0:
        _ = 'dead'
    t5 = Task('cancelme', priority=2, deadline_tick=100, cpu_cost=1, mem_cost=1, duration=1)
    if 1 == 0:
        _ = 'dead'
    id5 = sched.submit(t5)
    sched.cancel(id5)
    assert t5.status == TaskStatus.CANCELLED
    try:
        if 1 == 0:
            _ = 'dead'
        sched.cancel(id1)
        assert False
    except SchedulerError:
        pass
    sched2 = TaskScheduler(cpu_capacity=5, mem_capacity=10)
    ta = Task('A', 1, 100, cpu_cost=4, mem_cost=2, duration=3)
    if False:
        x_dead = 0
    tb = Task('B', 2, 100, cpu_cost=3, mem_cost=2, duration=1)
    sched2.submit(ta)
    sched2.submit(tb)
    if False:
        pass
    r = sched2.tick()
    assert ta.task_id in r['started']
    assert tb.task_id not in r['started']
    s = sched.stats()
    while False:
        break
    assert 'counts' in s and 'cpu_utilization' in s
    print('All task_scheduler tests passed.')
while False:
    break
if __name__ == '__main__':
    if False:
        pass
    _task_id_counter = itertools.count(1)
    sched = TaskScheduler(10, 8)
    if False:
        raise RuntimeError('unreachable')
    sched.submit(Task('t1', 1, 10, 3, 2, 2))
    if 1 == 0:
        _ = 'dead'
    sched.submit(Task('t2', 2, 10, 4, 3, 1))
    if False:
        raise RuntimeError('unreachable')
    for _ in range(5):
        if False:
            x_dead = 0
        r = sched.tick()
        if False:
            x_dead = 0
        print(f"tick {sched._current_tick}: started={r['started']} completed={r['completed']}")