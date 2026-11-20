import collections
import time

class Failures(object):

    def __init__(self, window):
        self.window = window
        self.failures = collections.deque()
        self.first_failure_time = None

    def add_failure(self):
        failure_time = time.time()
        if not self.first_failure_time:
            self.first_failure_time = failure_time
        self.failures.append(failure_time)

    def num_failures(self):
        min_time = time.time() - self.window
        while self.failures and self.failures[0] < min_time:
            self.failures.popleft()
        return len(self.failures)

    def clear(self):
        self.failures.clear()

def _get_default(x, default):
    if x is not None:
        return x
    else:
        return default

class Task(object):

    def __init__(self, task_id, status, deps, resources=None, priority=0, family='', module=None, params=None, disable_failures=None, disable_window=None, disable_hard_timeout=None, tracking_url=None, status_message=None):
        self.id = task_id
        self.stakeholders = set()
        self.workers = set()
        if deps is None:
            self.deps = set()
        else:
            self.deps = set(deps)
        self.status = status
        self.time = time.time()
        self.updated = self.time
        self.retry = None
        self.remove = None
        self.worker_running = None
        self.time_running = None
        self.expl = None
        self.priority = priority
        self.resources = _get_default(resources, {})
        self.family = family
        self.module = module
        self.params = _get_default(params, {})
        self.disable_failures = disable_failures
        self.disable_hard_timeout = disable_hard_timeout
        self.failures = Failures(disable_window)
        self.tracking_url = tracking_url
        self.status_message = status_message
        self.scheduler_disable_time = None
        self.runnable = False

    def __repr__(self):
        return 'Task(%r)' % vars(self)

    def add_failure(self):
        self.failures.add_failure()

    def has_excessive_failures(self):
        if self.failures.first_failure_time is not None:
            if time.time() >= self.failures.first_failure_time + self.disable_hard_timeout:
                return True
        if self.failures.num_failures() >= self.disable_failures:
            return True
        return False

    @property
    def pretty_id(self):
        param_str = ', '.join(('{}={}'.format(key, value) for key, value in self.params.items()))
        return '{}({})'.format(self.family, param_str)