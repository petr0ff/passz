import cycle

my_cycle = cycle.Cycle()
executions_to_process = my_cycle.get_executions_by_status_and_labels(my_cycle.status_from, my_cycle.labels)
for execution in executions_to_process:
    my_cycle.update_execution_status(execution, my_cycle.status_to)
