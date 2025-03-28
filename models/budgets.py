class Budgets: 
    def __init__(self, component_id, budget, period, core_id):
        self.component_id = component_id
        self.budget = float(budget)
        self.period = float(period)
        self.core_id = core_id


    def __repr__(self) -> str:
        return f"Component: {self.component_id} | Budget: {self.budget} | Period: {self.period} | CoreId: {self.core_id}" 
