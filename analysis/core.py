
class Core:
    def __init__(self, core_id, speed_factor, scheduler):
        self.core_id = core_id
        self.speed_factor = float(speed_factor)
        self.scheduler = scheduler
        self.components = []

class Component:
    def __init__(self, component_id, scheduler, budget, period, core_id, priority=None):
        self.component_id = component_id
        self.scheduler = scheduler
        self.budget = float(budget)
        self.period = float(period)
        self.core_id = core_id
        self.priority = float(priority) if priority and priority != "" else None
        self.tasks = []

class Task:
    def __init__(self, task_name, wcet, period, component_id, priority=None):
        self.task_name = task_name
        self.wcet = float(wcet)
        self.period = float(period)
        self.component_id = component_id
        self.priority = float(priority) if priority and priority != "" else None

class Solution:
    def __init__(self, task_name, component_id, task_schedulable, avg_response_time, max_response_time, component_schedulable):
        self.task_name = task_name
        self.component_id = component_id
        self.task_schedulable = int(task_schedulable) if task_schedulable != "" else 0
        self.avg_response_time = float(avg_response_time) if avg_response_time != "" else 0.0
        self.max_response_time = float(max_response_time) if max_response_time != "" else 0.0
        self.component_schedulable = int(component_schedulable) if component_schedulable != "" else 0