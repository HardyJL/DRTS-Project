class Task:
    def __init__(self, task_id, wcet, deadline, core_assignment):
        self.task_id = task_id
        self.wcet = wcet
        self.deadline = deadline
        self.core_assignment = core_assignment

    def __str__(self):
        return f"Task ID: {self.task_id}, WCET: {self.wcet}, Deadline: {self.deadline}, Core: {self.core_assignment}"

