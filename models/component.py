from models.task import Task
from models.job import Job # Assuming you create this class

class Component: 
    def __init__(self, component_id,scheduler ,budget, period, core_id):
        self.component_id = component_id
        self.budget = float(budget)  
        self.period = float(period)
        self.core_id = core_id
        self.scheduler = scheduler
        self.tasks: dict[str, Task] = {} # {task_name: task_obj}

        self.ready_queue: list[Job] = [] # Holds ready Job instances
        self.current_budget: float = 0.0 # Current remaining budget
        self.budget_refresh_time: int = 0 # Next cycle budget is replenished
        self.running_job: Job | None = None # Job currently running within this 

    def assign_task(self, task: Task):
        """Assigns a task to this component."""

        if task.component_ID == self.component_id:
            self.tasks[task.task_name] = task

        else:
            print(f"Warning: Task {task.task_name} component_id mismatch for Component {self.component_id}")


    def add_job_to_ready_queue(self, job: Job):
        """Adds a newly arrived job."""
        # Optionally sort immediately for EDF/RM if ready_queue is kept sorted
        self.ready_queue.append(job)


    def get_next_job_to_run(self) -> Job | None:
        """Selects the highest priority job based on the component scheduler."""
        if not self.ready_queue:
            return None
        if self.scheduler == "EDF":
            # Find job with earliest absolute deadline
            self.ready_queue.sort(key=lambda j: j.absolute_deadline)
            return self.ready_queue[0] # Highest priority is at the start
        elif self.scheduler == "RM":
             # Find job with highest priority (lowest number)
            self.ready_queue.sort(key=lambda j: j.task_ref.priority)
            return self.ready_queue[0] # Highest priority is at the start
        else:
            # Handle other/unknown schedulers if necessary
            return None
    
    def remove_job_from_ready_queue(self, job: Job):
        if job in self.ready_queue:
            self.ready_queue.remove(job)

    def replenish_budget(self):
        """Replenishes the component's budget."""
        self.current_budget = self.budget 
        self.budget_refresh_time += self.period

#Camera_Sensor,RM,8,13,Core_1
    def __repr__(self) -> str:
        return f"\nComponent: {self.component_id}| Scheduler: {self.scheduler} | Budget: {self.budget} | Period: {self.period} | CoreId: {self.core_id}" 
