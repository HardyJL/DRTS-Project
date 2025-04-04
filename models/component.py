from models import core

class Component: 
    def __init__(self, component_id,scheduler ,budget, period,core_id, core = None, tasks = None):
        self.component_id = component_id
        self.budget = float(budget)
        self.period = float(period)
        self.scheduler = scheduler
        self.core_id = core_id
        self.core = core 
        self.tasks = tasks 

    def __repr__(self):
        return f"\nComponent ID: {self.component_id}, Budget: {self.budget}, Period: {self.period}, Scheduler: {self.scheduler} | Core ID: {self.core_id} \n| Core: {self.core} \n| Tasks: {self.tasks}"
