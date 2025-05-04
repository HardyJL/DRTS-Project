class Task:
    def __init__(self, task_name, wcet, period, component_id, priority):
        self.task_name = task_name
        self.wcet = float(wcet)
        self.period = float(period)
        self.component_id = component_id
        if priority == "":
            self.priority = None
        else:
            self.priority = float(priority)
        self.remaining_time = float(wcet)
        # the starting time of the current execution
        self.current_start_time = 0
        # the list of response times of the task
        self.response_times = []
        self.schedulable = True

    def __repr__(self):
        return f"\nTask Name: {self.task_name}, WCET: {self.wcet}, Period: {self.period} | Priority: {self.priority}"
