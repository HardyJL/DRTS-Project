class Task:
    def __init__(self, task_name, wcet, period, component_ID, priority):
        self.task_name = task_name
        self.wcet = float(wcet)
        self.period = float(period)
        self.component_ID = component_ID
        if priority == "":
            self.priority=None
        else:
            self.priority = float(priority)
        self.current_execution = 0

    def __repr__(self):
        return f"\nTask Name: {self.task_name}, WCET: {self.wcet}, Period: {self.period} | Priority: {self.priority}"

