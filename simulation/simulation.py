import copy

from math import lcm
from models import Core, Component, Task, Solution
from scheduler import schedule_object
from csv_functions import write_solutions_to_csv


class Simulation:
    def __init__(self, cores: list[Core]):
        self.cores = cores

    def simulate(self, file: str) -> None:
        assert self.cores != None and len(self.cores) > 0, "No cores found"
        # Initialize the ready queue for each core
        # for each component in the ready queue inizialize the ready queue of tasks
        simulation_time = self.generate_core_components()
        while any(core.execution_time < simulation_time for core in self.cores):
            for core in self.cores:
                action_dict = {}
                # we caclulate the time that it takes until the next component is raised
                # and all components that need to be raised
                next_component_raise_time = sorted(
                    [c.period - core.execution_time % c.period for c in core.components])[0]
                next_components = [t for t in core.components if (
                    core.execution_time + next_component_raise_time) % t.period == 0]

                action_dict["raise_component"] = next_component_raise_time

                # only if we have an active component we will check for the ending of the component
                # and the tasks
                if len(core.ready_queue) > 0:
                    # get the first component in the ready queue scheduled correctly
                    core.ready_queue = schedule_object(
                        core.scheduler, core.ready_queue)
                    component: Component = core.ready_queue[0]
                    action_dict["finish_component"] = component.remaining_time

                    # in the event that we have finished a component and need to raise
                    # a task at the same time we need to check if they exist and basically
                    # run the simulation again for the same time frame
                    unraised_tasks = [t for t in component.tasks if core.execution_time >
                                      0 and t not in component.ready_queue and core.execution_time % t.period == 0]
                    if len(unraised_tasks) > 0:
                        component.raise_task(
                            unraised_tasks, core.execution_time, 0)
                        continue

                    # we caclulate the time that it takes until the next task is raised
                    # and all tasks that need to be raised
                    next_task_raise_time = sorted(
                        [c.period - core.execution_time % c.period for c in component.tasks])[0]
                    next_tasks = [t for t in component.tasks if (
                        core.execution_time + next_task_raise_time) % t.period == 0]
                    action_dict["raise_task"] = next_task_raise_time

                    # if there are currently active tasks we will check their finishing times
                    if len(component.ready_queue) > 0:
                        component.ready_queue = schedule_object(
                            component.scheduler, component.ready_queue)
                        task: Task = component.ready_queue[0]
                        action_dict["finish_task"] = task.remaining_time

                self.advance(action_dict, core, component,
                             task, next_components, next_tasks)

        self.generate_solutions(file)

    def advance(self, actions: dict, core: Core, component: Component, task: Task, next_components: list[Component], next_tasks: list[Task]):
        """Advances the simulation by the time of the lowest action
        and executes the action. The action is the one with the lowest time
        to the next event. The actions are:
        - raise_component: raises the next component
        - finish_component: finishes the current component
        - raise_task: raises the next task
        - finish_task: finishes the current task
        Args:
            actions (dict): A dictionary of actions and their time to the next event
            core (Core): the current core
            component (Component): the current component can be None
            task (Task): the current task can be None
            next_components (list[Component]): the next components to be raised can be empty
            next_tasks (list[Task]): the next tasks to be raised can be empty
        """
        action = min(actions, key=actions.get)
        action_value = actions[action]
        # remove all values that are not the lowest
        actions = {
            k: v for k, v in actions.items() if v == action_value}
        core.execution_time = round(
            core.execution_time + actions[action], 2)
        if "raise_component" in actions:
            core.raise_component(next_components, action_value)
        if "finish_component" in actions:
            core.finish_component(component, action_value)
        if "raise_task" in actions:
            # if we finish a task at the same time as we raise we dont want to double the time removed from the task
            if "finish_task" in actions:
                action_value = 0
            if component:
                component.raise_task(
                    next_tasks, core.execution_time, action_value)
        if "finish_task" in actions:
            if component and task:
                component.finish_task(
                    task, core.execution_time, action_value)

    def generate_core_components(self) -> float:
        """Generate the core components and their budgets
        Returns:
            float: the least common multiple of all components * 2
        """
        least_common_multiple_list = []
        for core in self.cores:
            core.components = schedule_object(core.scheduler, core.components)
            core.ready_queue = copy.copy(core.components)
            least_common_multiple_list.append(
                lcm(*[int(t.period) for t in core.components]))
            for component in core.components:
                component.tasks = schedule_object(
                    component.scheduler, component.tasks)
                least_common_multiple_list.append(
                    lcm(*[int(t.period) for t in component.tasks]))
                for task in component.tasks:
                    task.wcet = round(task.wcet / core.speed_factor, 2)
                    task.remaining_time = task.wcet
                component.ready_queue = copy.deepcopy(component.tasks)
        assert len(least_common_multiple_list) > 0, "No components found"
        return max(least_common_multiple_list) * 2

    def generate_solutions(self, file: str):
        """ Generate all solutions to print and to csv
        Args:
            file (str): the output file
        """
        all_solutions = []
        for core in self.cores:
            for component in core.components:
                component_schedulable = 1
                solutions = []
                for task in component.tasks:
                    task_schedulable = 0 if any(
                        r >= task.period for r in task.response_times) else 1
                    component_schedulable *= task_schedulable
                    average_resonse_time = round(sum(
                        task.response_times) / len(task.response_times), 2) if len(task.response_times) > 0 else 0
                    max_response_time = max(task.response_times) if len(
                        task.response_times) >= 1 else 0
                    sol = Solution(task_name=task.task_name, component_id=component.component_id,
                                   task_schedulable=task_schedulable, component_schedulable=0,
                                   avg_response_time=average_resonse_time, max_response_time=max_response_time)
                    solutions.append(sol)
                for s in solutions:
                    s.component_schedulable = component_schedulable
                    all_solutions.append(s)
        print(','.join(all_solutions[0].header()))
        for asl in all_solutions:
            print(asl)
        write_solutions_to_csv(solutions=all_solutions, filename=file)
