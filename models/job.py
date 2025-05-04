from models.task import Task

class Job:
    def __init__(self, task_ref: Task, arrival_time: int, core_speed_factor: float):
        self.task_ref = task_ref
        self.job_id = f"{task_ref.task_name}_{arrival_time}" # Example ID
        self.arrival_time = arrival_time
        # Assuming implicit deadline for now
        self.absolute_deadline = arrival_time + task_ref.period
        # Adjust WCET for core speed
        self.initial_wcet = task_ref.wcet / core_speed_factor
        self.remaining_wcet = self.initial_wcet
        self.state = "READY" # READY, RUNNING, COMPLETED
        self.start_time: int | None = None
        self.completion_time: int | None = None
        self.response_time: float | None = None

    def __repr__(self):
        return (f"Job({self.job_id}, rem={self.remaining_wcet:.2f}, "
                f"dl={self.absolute_deadline}, state={self.state})")