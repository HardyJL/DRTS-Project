import copy

from math import lcm
from typing import cast
from models import Core, Component, Task, Solution
from scheduler import schedule_object
from csv_functions import write_solutions_to_csv


class Simulation:
    def __init__(self, cores: list[Core]):
        self.cores = cores
        self.execution_time = 0.0

    def advance_clock(self, float) -> None:
        pass

    def finish_task(self, task: Task, component: Component) -> None:
        original_task = [
            t for t in component.tasks if t.task_name == task.task_name][0]
        self.execution_time = round(
            self.execution_time + task.remaining_time, 2)
        response_time = self.execution_time - task.current_start_time
        task.remaining_time = original_task.wcet
        original_task.response_times.append(round(response_time, 2))
        component.remaining_time -= task.remaining_time
        component.ready_queue.remove(task)

    def finish_component(self, component: Component, core: Core) -> None:
        self.execution_time = round(
            self.execution_time + component.remaining_time, 2)
        component.remaining_time = component.budget
        component.ready_queue[0].remaining_time -= component.remaining_time
        core.ready_queue.remove(component)

    def raise_component(self, time_until_next_raise: int, components_to_raise: list[Component], core: Core, advance: bool = False) -> None:
        if advance:
            self.execution_time = round(
                self.execution_time + time_until_next_raise, 2)
        for component in components_to_raise:
            core.ready_queue.append(component)

    def raise_task(self, time_until_next_raise: int, tasks_to_raise: list[Task], component: Component, advance: bool = False) -> None:
        if advance:
            self.execution_time = round(
                self.execution_time + time_until_next_raise, 2)
            component.remaining_time -= time_until_next_raise
            if len(component.ready_queue) > 0:
                next_up = component.ready_queue[0]
                next_up.remaining_time -= time_until_next_raise
        for task in tasks_to_raise:
            task.current_start_time = self.execution_time
            component.ready_queue.append(task)

    def test_simulate(self) -> None:
        assert self.cores != None and len(self.cores) > 0, "No cores found"
        print("==========Simulating==========")
        # Initialize the ready queue for each core
        # for each component in the ready queue inizialize the ready queue of tasks
        simulation_time = self.generate_core_components()
        while self.execution_time < simulation_time:
            print(f"{self.execution_time} / {simulation_time}")
            for core in self.cores:

                difference_to_next_component_raise = sorted(
                    [c.period - self.execution_time % c.period for c in core.components])[0]
                next_raised_components = [t for t in core.components if (
                    self.execution_time + difference_to_next_component_raise) % t.period == 0]

                if len(core.ready_queue) < 1:
                    self.raise_component(
                        difference_to_next_component_raise, next_raised_components, core, advance=True)
                    continue

                component = schedule_object(
                    core.scheduler, core.ready_queue)[0]
                
                print(component.component_id)


                # print(
                #     f"Component {component.component_id} - {component.scheduler} - {component.budget} - {component.period} - {self.execution_time}")

                difference_to_next_task_raise = sorted(
                    [c.period - self.execution_time % c.period for c in component.tasks])[0]
                next_raised_tasks = [t for t in component.tasks if (
                    self.execution_time + difference_to_next_task_raise) % t.period == 0]

                if len(component.ready_queue) < 1:
                    self.raise_task(difference_to_next_task_raise, next_raised_tasks,
                                    component, advance=True)
                    continue

                print([t.task_name for t in component.ready_queue])

                next_task_done = schedule_object(
                    component.scheduler, component.ready_queue)[0]

                action_dict = {
                    "raise_component": difference_to_next_component_raise,
                    "raise_task": difference_to_next_task_raise,
                    "finish_task": next_task_done.remaining_time,
                    "finish_component": component.remaining_time,
                }
                # find the lowest value in the action dict
                action = min(action_dict, key=action_dict.get)
                # remove all values that are not the lowest
                action_dict = {
                    k: v for k, v in action_dict.items() if v == action_dict[action]}

                print(f"{action_dict}")

                if "raise_component" in action_dict:
                    self.raise_component(
                        difference_to_next_component_raise, next_raised_components, core)
                if "raise_task" in action_dict:
                    advance = False if (len(action_dict) > 1) else True
                    self.raise_task(difference_to_next_task_raise, next_raised_tasks,
                                    component, advance=True)
                if "finish_task" in action_dict:
                    self.finish_task(next_task_done, component)
                if "finish_component" in action_dict:
                    self.finish_component(component, core)
                # if we have a task that is not finished and the component is not finished

                # if component.remaining_time < difference_to_next_task_raise and component.remaining_time < next_task_done.remaining_time:
                #     self.finish_component(component, core)
                #     continue

                # if next_task_done.remaining_time < difference_to_next_task_raise:
                #     self.finish_task(next_task_done, component)
                # elif next_task_done.remaining_time == difference_to_next_task_raise:
                #     self.finish_task(next_task_done, component)
                #     self.raise_task(difference_to_next_task_raise,
                #                     next_raised_tasks, component)
                # else:
                #     self.raise_task(difference_to_next_task_raise, next_raised_tasks,
                #                     component, advance=True)

        print(f"{self.execution_time} / {simulation_time}")
        print("=============Done=============")

        for core in self.cores:
            for component in core.components:
                for task in component.tasks:
                    print(
                        f"Component - {component.component_id} - Task {task.task_name} - WCET {task.wcet} - Period {task.period} - Response times {task.response_times}")

    def simulate(self, simulation_time_factor: int, file: str) -> None:
        """ Function that simulates the given cores execution
        this returns nothing but creates a xml file which holds the values for average responste times and worst case response time
        Args:
            simulation_time_factor (int): multiplication factor for the longest task
            we will run the longest task at least this amount of times
            file: str the output file
        """
        assert self.cores != None and len(self.cores) > 0, "No cores found"
        print("Simulating...")
        # Initialize the ready queue for each core
        # for each component in the ready queue inizialize the ready queue of tasks
        simulation_time = self.generate_core_components()
        simulation_time *= simulation_time_factor
        current_time = 0.0
        while current_time < simulation_time:
            advance_increment = self.advance_time(current_time)
            for core in self.cores:
                self.update_ready_queue(core, current_time)
                if len(core.ready_queue) > 0:
                    component: Component = schedule_object(
                        core.scheduler, core.ready_queue)[0]
                    # if we have a component to execute we go ahead and update the values
                    # if the component has not started we set the start time
                    self.check_if_started(component, current_time)
                    # get the ready queue of the tasks
                    self.update_ready_queue(component, current_time)
                    if len(component.ready_queue) > 0:
                        current_task: Task = schedule_object(
                            component.scheduler, component.ready_queue)[0]
                        print(
                            f"Component {component.component_id, component.scheduler, component.budget, component.period} - {current_task.task_name, current_task.wcet, current_task.period} - {current_time}")
                        self.check_if_started(current_task, current_time)
                        current_task.current_execution += advance_increment
                        if self.check_if_ended(current_task, current_time):
                            component.ready_queue.remove(current_task)
                    # if we have reached the end of the component we keep the response time
                    # and reset the execution time
                    # increase the execution time by one
                    component.current_execution += advance_increment
                    if self.check_if_ended(component, current_time):
                        core.ready_queue.remove(component)
            current_time = round(current_time + advance_increment, 2)

        self.generate_solutions(file)

    def check_if_started(self, obj: Component | Task, current_time: int) -> None:
        """Checks if the current task or component has started
        if not we set the starting time of the task/component execution to the  current time

        Args:
            obj (Component | Task): Task/Component that we are going to check  
            current_time (int): the time of the check
        """
        if obj.current_start_time == 0:
            obj.current_start_time = current_time

    def check_if_ended(self, obj: Component | Task, current_time: int) -> bool:
        """Checks if the current task or component has finished
        if yes we remeber the time that it took and reset the counters
        Args:
            obj (Component | Task): Task/Component that we are going to check  
            current_time (int): the time of the check
        Returns:
            bool: Returns whether or not the operation was successfull
        """
        # select the comparing value based on the type of obj
        comparing_value = obj.budget if type(
            obj) is Component else cast(Task, obj).wcet
        # checks if we have reached the end of the execution
        if obj.current_execution > comparing_value:
            if type(obj) is Task:
                amounts_raised = current_time // obj.period
                last_raise = amounts_raised * obj.period
                response_time = current_time - last_raise
                obj.response_times.append(round(response_time, 2))
            # reset execution time and start time
            obj.current_execution = 0
            obj.current_start_time = 0
            return True
        return False

    def update_ready_queue(self, obj: Core | Component, current_time: float):
        """Update the ready queue for a core or a component depending on the current time.
        Args:
            obj (Core | Component): the object that we need to change
            current_time (float): the current execution time
        """
        if (current_time == 0):
            return
        assert isinstance(obj, Core) or isinstance(obj, Component)
        if type(obj) is Core:
            obj.ready_queue += [t for t in obj.components if current_time %
                                t.period == 0.0]
        elif type(obj) is Component:
            obj.ready_queue += [t for t in obj.tasks if current_time %
                                t.period == 0.0]

    def generate_core_components(self) -> float:
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
        return max(least_common_multiple_list)

    def advance_time(self, current_time: float) -> float:
        """ returns the advancement in time that is needed to go to the next task
        Args:
            current_time (float): the current time
        Returns:
            float: the calculated result
        """
        next_time = []
        for core in self.cores:
            for component in core.components:
                if len(component.ready_queue) < 1:
                    next_time.append(
                        min([c.period - (current_time % c.period) for c in component.tasks]))
                else:
                    return 0.1
        return min(next_time)

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
        # write_solutions_to_csv(solutions=all_solutions, filename=file)
