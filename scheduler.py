from typing import cast

from .models import Task

class Scheduler:
    """
    Base class for scheduling algorithms.
    """
    def __init__(self):
        return

    def rate_monotonic(self, list: list[Task]) -> list[Task]:
        """
        Rate Monotonic Scheduling Algorithm
        :param list[Task] list of tasks
        :return: list of tasks in order of execution
        """
        assert(task for task in list if task.priority is not None), "Task priority must be set"
        sorted_tasks = sorted(list, key=lambda task: cast(float,task.priority))
        return sorted_tasks

    def earliest_deadline_first(self, list: list[Task]) -> list[Task]:
        """
        Earliest Deadline First Scheduling Algorithm
        :param list[Task] list of tasks
        :return: list of tasks in order of execution
        """
        sorted_tasks = sorted(list, key=lambda task: task.period)
        return sorted_tasks

