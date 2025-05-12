from typing import List, Optional, Union 

class Task:
    def __init__(self, task_name: str,
                 wcet: Union[str, float],        # Can be string or float
                 period: Union[str, float],       # Can be string or float
                 component_id: str,
                 priority: Optional[Union[str, float]] = None, # Can be string, float, or None
                 task_type: Optional[str] = "periodic",
                 deadline: Optional[Union[str, float]] = None): # Can be string, float, or None

        self.task_name = task_name
        
        # Handle wcet
        if isinstance(wcet, str):
            self.original_wcet = float(wcet) if wcet and wcet.strip() != "" else 0.0
        else: # Assumed float or int
            self.original_wcet = float(wcet)
        self.wcet = self.original_wcet # This will be adjusted by speed_factor later

        # Handle period (which is MIT for sporadic)
        if isinstance(period, str):
            self.period = float(period) if period and period.strip() != "" else 0.0
        else: # Assumed float or int
            self.period = float(period)
        if self.period == 0: # Avoid division by zero issues later
            print(f"Warning: Task {self.task_name} has period/MIT of 0. Setting to 1.0 to avoid errors.")
            self.period = 1.0


        self.component_id = component_id
        
        # Handle priority
        if priority is None or (isinstance(priority, str) and priority.strip() == ""):
            self.priority = None
        elif isinstance(priority, str):
            self.priority = float(priority)
        else: # Assumed float or int
            self.priority = float(priority)
        
        # Handle task_type
        self.task_type = task_type if task_type and task_type.strip() != "" else "periodic"
        
        # Handle deadline
        if deadline is None or (isinstance(deadline, str) and deadline.strip() == ""):
            self.deadline = self.period # Default deadline to period/MIT
        elif isinstance(deadline, str):
            self.deadline = float(deadline) if deadline.strip() != "" else self.period
        else: # Assumed float or int
            self.deadline = float(deadline)
        
        # Ensure deadline is not zero if period is not zero
        if self.deadline == 0 and self.period != 0:
            print(f"Warning: Task {self.task_name} has deadline 0 with non-zero period/MIT. Setting deadline to period/MIT.")
            self.deadline = self.period


    def __repr__(self):
        return (f"Task(name={self.task_name}, type={self.task_type}, wcet={self.wcet:.2f} (orig: {self.original_wcet:.2f}), "
                f"period/MIT={self.period}, deadline={self.deadline}, prio={self.priority}, comp={self.component_id})")


class Component:
    def __init__(self, component_id: str, scheduler: str,
                 budget: Union[str, float],
                 period: Union[str, float],
                 core_id: str,
                 priority: Optional[Union[str, float]] = None,
                 server_budget: Optional[Union[str, float]] = None,
                 server_period: Optional[Union[str, float]] = None):
        self.component_id = component_id
        self.scheduler = scheduler
        
        self.budget = float(budget) if isinstance(budget, (int, float)) else (float(budget) if budget and budget.strip() != "" else 0.0)
        self.period = float(period) if isinstance(period, (int, float)) else (float(period) if period and period.strip() != "" else 1.0)
        if self.period == 0: self.period = 1.0 # Avoid division by zero

        self.core_id = core_id
        
        if priority is None or (isinstance(priority, str) and priority.strip() == ""):
            self.priority = None
        else:
            self.priority = float(priority) if isinstance(priority, (int,float)) else float(priority)

        self.server_budget = float(server_budget) if isinstance(server_budget, (int,float)) else (float(server_budget) if server_budget and str(server_budget).strip() != "" else None)
        self.server_period = float(server_period) if isinstance(server_period, (int,float)) else (float(server_period) if server_period and str(server_period).strip() != "" else None)
        if self.server_period == 0: self.server_period = None # Server period cannot be 0

        self.tasks: List[Task] = []
        self.polling_server_task: Optional[Task] = None

    def __repr__(self):
        return (f"Component(id={self.component_id}, scheduler={self.scheduler}, budget={self.budget}, period={self.period}, "
                f"core={self.core_id}, prio={self.priority}, server_budget={self.server_budget}, server_period={self.server_period})")


class Core:
    def __init__(self, core_id: str, speed_factor: str, scheduler: str):
        self.core_id = core_id
        self.speed_factor = float(speed_factor)
        self.scheduler = scheduler
        self.components: List[Component] = []

    def __repr__(self):
        return (f"Core(id={self.core_id}, speed={self.speed_factor}, scheduler={self.scheduler})")


class Solution:
    def __init__(self, task_name, component_id, task_schedulable, avg_response_time, max_response_time, component_schedulable):
        self.task_name = task_name
        self.component_id = component_id
        self.task_schedulable = int(task_schedulable) if task_schedulable != "" else 0
        self.avg_response_time = float(avg_response_time) if avg_response_time != "" else 0.0
        self.max_response_time = float(max_response_time) if max_response_time != "" else 0.0
        self.component_schedulable = int(component_schedulable) if component_schedulable != "" else 0

    def header(self): # Method to get header for CSV writing
        return ['task_name', 'component_id', 'task_schedulable', 'avg_response_time', 'max_response_time', 'component_schedulable']