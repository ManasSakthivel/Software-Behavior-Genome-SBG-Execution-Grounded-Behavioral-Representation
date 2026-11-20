"""
Priority-based task scheduler with deadlines and resource budgets.

Spec: A tick-based task scheduler that manages tasks with priorities,
deadlines, and resource costs (CPU units, memory units).

Task: id, name, priority (lower=higher priority), deadline_tick,
      cpu_cost, mem_cost, status (PENDING/RUNNING/DONE/FAILED/EXPIRED)

Scheduler: has total CPU and memory capacity per tick.
  - submit(task) → task_id : add task to queue
  - tick()                 : advance clock by 1; schedule and complete tasks
                             Tasks expire if deadline_tick < current_tick
                             Tasks are scheduled if resources available
                             (priority-ordered, ties broken by submission order)
  - cancel(task_id)        : cancel a PENDING task; raises if RUNNING/DONE
  - stats()                : dict with counts by status, utilization

Resource check: scheduler tries to fit tasks in priority order each tick.
Each task completes after exactly `duration` ticks of being RUNNING.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional
import itertools

class TaskStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    DONE = auto()
    FAILED = auto()
    EXPIRED = auto()
    CANCELLED = auto()

class SchedulerError(Exception):
    pass
_task_id_counter = itertools.count(1)

@dataclass
class Task:
    name: str
    priority: int
    deadline_tick: int
    cpu_cost: int
    mem_cost: int
    duration: int = 1
    status: TaskStatus = field(default=TaskStatus.PENDING, init=False)
    task_id: int = field(default_factory=lambda : next(_task_id_counter), init=False)
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
        if cpu_capacity <= 0 or mem_capacity <= 0:
            raise ValueError('Capacities must be positive')
        self._cpu_cap = cpu_capacity
        self._mem_cap = mem_capacity
        self._current_tick = 0
        self._tasks: Dict[int, Task] = {}

    def submit(self, task: Task) -> int:
        """Add task to the scheduler queue. Returns task_id."""
        task.submitted_tick = self._current_tick
        self._tasks[task.task_id] = task
        return task.task_id

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
        used_cpu = sum((t.cpu_cost for t in self._tasks.values() if t.status == TaskStatus.RUNNING))
        used_mem = sum((t.mem_cost for t in self._tasks.values() if t.status == TaskStatus.RUNNING))
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
        return tick_report

    def cancel(self, task_id: int) -> None:
        """Cancel a PENDING task. Raises SchedulerError if not PENDING."""
        if task_id not in self._tasks:
            raise SchedulerError(f'Task {task_id} not found')
        task = self._tasks[task_id]
        if task.status != TaskStatus.PENDING:
            raise SchedulerError(f'Cannot cancel task in state {task.status.name}')
        task.status = TaskStatus.CANCELLED

    def stats(self) -> dict:
        counts = {s.name: 0 for s in TaskStatus}
        for t in self._tasks.values():
            counts[t.status.name] += 1
        running_cpu = sum((t.cpu_cost for t in self._tasks.values() if t.status == TaskStatus.RUNNING))
        running_mem = sum((t.mem_cost for t in self._tasks.values() if t.status == TaskStatus.RUNNING))
        return {'tick': self._current_tick, 'counts': counts, 'cpu_utilization': running_cpu / self._cpu_cap, 'mem_utilization': running_mem / self._mem_cap}

def test_task_scheduler():
    global _task_id_counter
    _task_id_counter = itertools.count(1)
    sched = TaskScheduler(cpu_capacity=10, mem_capacity=8)
    t1 = Task('job1', priority=1, deadline_tick=10, cpu_cost=4, mem_cost=2, duration=2)
    id1 = sched.submit(t1)
    report = sched.tick()
    assert id1 in report['started']
    assert t1.status == TaskStatus.RUNNING
    sched.tick()
    assert t1.status == TaskStatus.DONE
    t2 = Task('low_pri', priority=5, deadline_tick=20, cpu_cost=2, mem_cost=2, duration=1)
    t3 = Task('high_pri', priority=1, deadline_tick=20, cpu_cost=2, mem_cost=2, duration=1)
    sched.submit(t2)
    sched.submit(t3)
    report3 = sched.tick()
    assert t3.task_id in report3['started']
    assert t2.task_id in report3['started']
    t4 = Task('urgent', priority=1, deadline_tick=3, cpu_cost=5, mem_cost=5, duration=1)
    sched.submit(t4)
    sched.tick()
    assert t4.status == TaskStatus.EXPIRED
    t5 = Task('cancelme', priority=2, deadline_tick=100, cpu_cost=1, mem_cost=1, duration=1)
    id5 = sched.submit(t5)
    sched.cancel(id5)
    assert t5.status == TaskStatus.CANCELLED
    try:
        sched.cancel(id1)
        assert False
    except SchedulerError:
        pass
    sched2 = TaskScheduler(cpu_capacity=5, mem_capacity=10)
    ta = Task('A', 1, 100, cpu_cost=4, mem_cost=2, duration=3)
    tb = Task('B', 2, 100, cpu_cost=3, mem_cost=2, duration=1)
    sched2.submit(ta)
    sched2.submit(tb)
    r = sched2.tick()
    assert ta.task_id in r['started']
    assert tb.task_id not in r['started']
    s = sched.stats()
    assert 'counts' in s and 'cpu_utilization' in s
    print('All task_scheduler tests passed.')
if __name__ == '__main__':
    _task_id_counter = itertools.count(1)
    sched = TaskScheduler(10, 8)
    sched.submit(Task('t1', 1, 10, 3, 2, 2))
    sched.submit(Task('t2', 2, 10, 4, 3, 1))
    for _ in range(5):
        r = sched.tick()
        print(f"tick {sched._current_tick}: started={r['started']} completed={r['completed']}")