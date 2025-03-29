class Budgets: 
    def __init__(self, component_id,scheduler ,budget, period, core_id):
        self.component_id = component_id
        self.budget = float(budget)
        self.period = float(period)
        self.core_id = core_id
        self.scheduler = scheduler

#Camera_Sensor,RM,8,13,Core_1
    def __repr__(self) -> str:
        return f"\nComponent: {self.component_id}| Scheduler: {self.scheduler} | Budget: {self.budget} | Period: {self.period} | CoreId: {self.core_id}" 
