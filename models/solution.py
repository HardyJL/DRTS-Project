class Solution:
    def __init__(self, task_name, component_id, task_schedulable, avg_response_time, max_response_time, component_schedulable) -> None:
        self.task_name = task_name
        self.component_id = component_id
        self.task_schedulable = int(task_schedulable)
        self.avg_response_time = float(avg_response_time)
        self.max_response_time = float(max_response_time)
        self.component_schedulable = int(component_schedulable)

    def __repr__(self) -> str:
        return f"{self.task_name} | {self.component_id} | {self.task_schedulable} | {self.avg_response_time} | {self.max_response_time} | {self.component_schedulable}" 
