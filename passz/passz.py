import cycle

my_cycle = cycle.Cycle()
executions_to_process = my_cycle.get_executions_by_status_and_labels("UNEXECUTED", ["automated"])
for execution in executions_to_process:
    my_cycle.update_execution_status(execution, "PASS")
