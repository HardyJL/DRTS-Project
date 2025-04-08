from typing import cast

from models import Task

def earliest_deadline_first(tasks: list[Task]) -> list[Task]:
    return sorted(tasks, key=lambda task: cast(float, task.wcet))

def fixed_priority_with_rm(tasks: list[Task]) -> list[Task]:
    return sorted(tasks, key=lambda task: task.period)
