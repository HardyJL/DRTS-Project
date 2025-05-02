from typing import cast
from models import Core, Component, Task, Solution
from scheduler import schedule_object
from csv_functions import write_solutions_to_csv


class Simulation:
    def __init__(self, cores: list[Core]):
        self.cores = cores

    def simulate(self, simulation_time_factor: int,file) -> None:
        """
        Function that simulates the given cores execution
        this returns nothing but creates a xml file which holds the values for average responste times and worst case response time
        Args:
            simulation_time_factor (int): multiplication factor for the longest task
            we will run the longest task at least this amount of times
        """
        def check_if_started(obj: Component | Task, current_time: int) -> None:
            """
            Checks if the current task or component has started
            if not we set the starting time of the task/component execution to the  current time

            Args:
                obj (Component | Task): Task/Component that we are going to check  
                current_time (int): the time of the check
            """
            if obj.current_start_time == 0:
                obj.current_start_time = current_time

        def check_if_ended(obj: Component | Task, current_time: int) -> bool:
            """
            Checks if the current task or component has finished
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
                    obj.response_times.append(response_time)
                # reset execution time and start time
                obj.current_execution = 0
                obj.current_start_time = 0
                return True
            return False

        assert self.cores != None and len(self.cores) > 0, "No cores found"
        print("Simulating...")
        # Initialize the ready queue for each core
        # for each component in the ready queue inizialize the ready queue of tasks
        simulation_time = self.generate_core_components()
        simulation_time *= simulation_time_factor
        current_time = 0
        while current_time < simulation_time:
            print(current_time)
            advance_increment = self.advance_time(current_time=current_time)
            for core in self.cores:
                core.ready_queue += [t for t in core.components if current_time %
                                     t.period == 0]
                if len(core.ready_queue) > 0:
                    component: Component = schedule_object(
                        core.scheduler, core.ready_queue)[0]
                    # if we have a component to execute we go ahead and update the values
                    # if the component has not started we set the start time
                    check_if_started(component, current_time)
                    # get the ready queue of the tasks
                    component.ready_queue += [
                        t for t in component.tasks if current_time % t.period == 0]
                    if len(component.ready_queue) > 0:
                        current_task: Component = schedule_object(
                            component.scheduler, component.ready_queue)[0]
                        check_if_started(current_task, current_time)
                        current_task.current_execution += advance_increment
                        if check_if_ended(current_task, current_time):
                            component.ready_queue.remove(current_task)
                    # if we have reached the end of the component we keep the response time
                    # and reset the execution time
                    # increase the execution time by one
                    component.current_execution += advance_increment    
                    if check_if_ended(component, current_time):
                        core.ready_queue.remove(component)
            current_time += advance_increment

        self.generate_solutions(file=file)
    
    def generate_core_components(self) -> int:    
        simulation_time = 0
        for core in self.cores:
            core.components = schedule_object(core.scheduler, core.components)
            for component in core.components:
                component.tasks = schedule_object(
                    component.scheduler, component.tasks)
                for task in component.tasks:
                    task.wcet = task.wcet / core.speed_factor
                    if task.period > simulation_time:
                        simulation_time = task.period
        return simulation_time

    def advance_time(self, current_time: int) -> int:
        next_time = []
        for core in self.cores:
            if len(core.ready_queue) < 1:
                next_time.append((min([c.period - (current_time % c.period) for c in core.components])))
            else:
                for component in core.components:
                    if len(component.ready_queue) < 1:
                        next_time.append(min([c.period - (current_time % c.period) for c in component.tasks]))
                    else:
                        return 1    
        return min(next_time)
    
    def generate_solutions(self, file: str):
        all_solutions = []
        for core in self.cores:
            for component in core.components:
                component_schedulable = 1
                solutions = []
                for task in component.tasks:
                    task_schedulable = 0 if any(r >= task.period for r in task.response_times) else 1
                    component_schedulable *= task_schedulable
                    average_resonse_time = round(sum(
                        task.response_times) / len(task.response_times),2) if len(task.response_times) > 0 else -1
                    max_response_time = max(task.response_times) if len(
                        task.response_times) >= 1 else -1
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
