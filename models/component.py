from . import Task
class Component: 
    def __init__(self, component_id,scheduler, budget, period, core_id, priority):
        self.component_id = component_id
        self.budget = float(budget)
        self.period = float(period)
        self.scheduler = scheduler
        self.core_id = core_id
        self.priority = priority

        self.tasks: list[Task] = [] 
        self.ready_queue: list[Task] = []
        # the current exection time of the component
        self.remaining_time = float(budget)
        # the starting time of the current execution
        self.current_start_time = 0


    def __repr__(self):
        return f"\nComponent ID = ({self.component_id}) | Budget ({self.budget}) | Period ({self.period}) | Scheduler ({self.scheduler}) \n Tasks: {self.tasks}"

    def __eq__(self, other):
        assert isinstance(other, Component)
        return self.period == other.period
    
    def __lt__(self, other): 
        assert isinstance(other, Component)
        return self.period < other.period

