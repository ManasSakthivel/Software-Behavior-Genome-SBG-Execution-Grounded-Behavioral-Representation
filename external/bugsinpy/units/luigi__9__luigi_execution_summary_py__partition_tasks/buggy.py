# BugsInPy luigi/9 | https://github.com/spotify/luigi | luigi/execution_summary.py | unit _partition_tasks
# license: Apache-2.0 (upstream project); extracted verbatim, closure only, no edits
# commit f7e0b7710fd8b12f27625b1efb62a8fde6e206c4 (buggy)
def _partition_tasks(worker):
    """
    Takes a worker and sorts out tasks based on their status.
    Still_pending_not_ext is only used to get upstream_failure, upstream_missing_dependency and run_by_other_worker
    """
    task_history = worker._add_task_history
    pending_tasks = {task for(task, status, ext) in task_history if status == 'PENDING'}
    set_tasks = {}
    set_tasks["completed"] = {task for (task, status, ext) in task_history if status == 'DONE' and task in pending_tasks}
    set_tasks["already_done"] = {task for (task, status, ext) in task_history
                                 if status == 'DONE' and task not in pending_tasks and task not in set_tasks["completed"]}
    set_tasks["failed"] = {task for (task, status, ext) in task_history if status == 'FAILED'}
    set_tasks["scheduling_error"] = {task for(task, status, ext) in task_history if status == 'UNKNOWN'}
    set_tasks["still_pending_ext"] = {task for (task, status, ext) in task_history
                                      if status == 'PENDING' and task not in set_tasks["failed"] and task not in set_tasks["completed"] and not ext}
    set_tasks["still_pending_not_ext"] = {task for (task, status, ext) in task_history
                                          if status == 'PENDING' and task not in set_tasks["failed"] and task not in set_tasks["completed"] and ext}
    set_tasks["run_by_other_worker"] = set()
    set_tasks["upstream_failure"] = set()
    set_tasks["upstream_missing_dependency"] = set()
    set_tasks["upstream_run_by_other_worker"] = set()
    set_tasks["upstream_scheduling_error"] = set()
    set_tasks["not_run"] = set()
    return set_tasks
