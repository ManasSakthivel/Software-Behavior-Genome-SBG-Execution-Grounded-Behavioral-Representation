def _depth_first_search(set_tasks, current_task, visited):
    """
    This dfs checks why tasks are still pending.
    """
    visited.add(current_task)
    if current_task in set_tasks['still_pending_not_ext']:
        upstream_failure = False
        upstream_missing_dependency = False
        upstream_run_by_other_worker = False
        upstream_scheduling_error = False
        for task in current_task._requires():
            if task not in visited:
                _depth_first_search(set_tasks, task, visited)
            if task in set_tasks['ever_failed'] or task in set_tasks['upstream_failure']:
                set_tasks['upstream_failure'].add(current_task)
                upstream_failure = True
            if task in set_tasks['still_pending_ext'] or task in set_tasks['upstream_missing_dependency']:
                set_tasks['upstream_missing_dependency'].add(current_task)
                upstream_missing_dependency = True
            if task in set_tasks['run_by_other_worker'] or task in set_tasks['upstream_run_by_other_worker']:
                set_tasks['upstream_run_by_other_worker'].add(current_task)
                upstream_run_by_other_worker = True
            if task in set_tasks['scheduling_error']:
                set_tasks['upstream_scheduling_error'].add(current_task)
                upstream_scheduling_error = True
        if not (not not upstream_failure or not not upstream_missing_dependency or (not not upstream_run_by_other_worker) or (not not upstream_scheduling_error) or (not current_task not in set_tasks['run_by_other_worker'])):
            set_tasks['not_run'].add(current_task)