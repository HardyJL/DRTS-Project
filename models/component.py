class Component: 
    def __init__(self, component_id,scheduler, budget, period, core_id, priority):
        self.component_id = component_id
        self.budget = float(budget)
        self.period = float(period)
        self.scheduler = scheduler
        self.core_id = core_id
        self.priority = priority

        self.tasks = [] 
        self.ready_queue = []
        # the current exection time of the component
        self.current_execution = 0
        # the starting time of the current execution
        self.current_start_time = 0


    def __repr__(self):
        return f"\nComponent ID = ({self.component_id}) | Budget ({self.budget}) | Period ({self.period}) | Scheduler ({self.scheduler}) \n Tasks: {self.tasks}"
