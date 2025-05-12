from . import Task


class Component:
    def __init__(self, component_id, scheduler, budget, period, core_id, priority,server_priority=0,server_period=0):
        self.component_id = component_id
        self.budget = float(budget)
        self.period = float(period)
        self.scheduler = scheduler
        self.core_id = core_id
        self.priority = priority
        self.tasks: list[Task] = []
        self.ready_queue: list[Task] = []
        self.remaining_time = float(budget)
        self.current_start_time = 0
        self.server_priority = server_priority
        self.server_period = server_period

    def __repr__(self):
        return f"\nComponent ID = ({self.component_id}) | Budget ({self.budget}) | Period ({self.period}) | Scheduler ({self.scheduler}) \n Tasks: {self.tasks}"

    def finish_task(self, task: Task, execution_time: int, time_difference: int) -> None:
        """Finishes the given task and reduces the 
        remaining time of the task and components to the correct values.

        Args:
            task (Task): The task to finish
            execution_time (int): the execution time of the task
            time_difference (int): the time difference between the current time and finish time 
        """
        original_task = [
            t for t in self.tasks if t.task_name == task.task_name][0]
        response_time = execution_time - task.current_start_time
        task.remaining_time = original_task.wcet
        original_task.response_times.append(round(response_time, 2))
        self.remaining_time -= time_difference
        self.ready_queue.remove(task)

    def raise_task(self, tasks_to_raise: list[Task], execution_time: int, time_difference: int) -> None:
        """Raises all given tasks and recuces the 
        remaining time of the task and components to the correct values.

        Args:
            tasks_to_raise (list[Task]): The tasks to raise
            execution_time (int): the current core execution time
            time_difference (int): the time difference between the current time and the finish time
        """
        if len(self.ready_queue) > 0:
            self.ready_queue[0].remaining_time -= time_difference
        self.remaining_time -= time_difference
        for task in tasks_to_raise:
            task.current_start_time = execution_time
            self.ready_queue.append(task)
