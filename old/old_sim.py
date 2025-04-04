from ..models import Task

## function for
def simulate(tasks: list[Task], simulation_time_factor: int):
    """
    Simulates the execution of the given task list

    Args:
        tasks (list[Task]): List of tasks to be simulated.
        simulation_time_factor (int): Factor to extend the simulation time by the highest period task.

    Returns:
        None
    """
    # Extend simulation time by the maximum period of the tasks
    simulation_time = get_max_period(tasks) * simulation_time_factor
    current_time = 0
    ready_queue = []

    # Main simulation loop
    while current_time <= simulation_time:
        # Add tasks that are ready to the ready_queue
        add_ready_tasks(ready_queue, tasks, current_time)
        # Get the highest priority task from the ready_queue
        current_job = get_highest_priority_task(ready_queue)
        
        if current_job:
            # Process the current job
            process_current_job(current_job, current_time)
            current_time += advance_time()
            # If the current job is completed, update its completion status and remove it from the ready_queue
            if current_job.remaining_time <= 0:
                update_task_completion(current_job, current_time)
                ready_queue.remove(current_job)
        else:
            # If no job is ready, increment the current time
            current_time += advance_time()

    # Print the final status of all tasks
    print_tasks(tasks)

def advance_time() -> int:
    return 1

def get_max_period(tasks: list[Task]) -> int:
    # Return the maximum period among all tasks
    return sorted(tasks, key=lambda t: t.period, reverse=True)[0].period

def add_ready_tasks(ready_queue: list[Task], tasks: list[Task], current_time: int):
    # Add tasks to the ready_queue if they are ready at the current time
    ready_queue += [t for t in tasks if current_time % t.period == 0]

def get_highest_priority_task(ready_queue: list[Task]) -> Task:
    # Return the task with the highest priority from the ready_queue, or None if the queue is empty
    return sorted(ready_queue, key=lambda t: t.priority)[0] if ready_queue else None

def process_current_job(current_job: Task, current_time: int):
    # If the job has not started, mark it as started and set its release time
    if not current_job.has_started:
        current_job.has_started = True
        current_job.release = current_time
    # Decrement the remaining time of the current job
    current_job.remaining_time -= advance_time()

def update_task_completion(current_job: Task, current_time: int):
    # Update the worst-case response time (WCRT) of the current job
    current_job.wcrt = max(current_job.wcrt, current_time - current_job.release)
    # Reset the job's status and remaining time
    current_job.has_started = False
    current_job.remaining_time = current_job.calculated_execution_time

def print_tasks(tasks: list[Task]):
    # Print the details of each task
    for task in tasks:
        print(task)
