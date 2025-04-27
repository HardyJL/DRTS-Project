from typing import cast
from models import Core, Component, Task
from scheduler import schedule_object

class Simulation:
    def __init__(self, cores: list[Core], simulation_time: int):
        self.cores = cores
        self.simulation_time = simulation_time

    def simulate(self):
        def check_if_started(obj: Component | Task, current_time: int) -> None:
            if obj.current_start_time == 0:
                obj.current_start_time = current_time

        def check_if_ended(obj: Component | Task, current_time: int) -> bool:
            comparing_value = obj.budget if type(obj) is Component else cast(Task, obj).wcet
            if obj.current_execution >= comparing_value:
                obj.response_times.append(current_time - obj.current_start_time)
                if type(obj) is Component:
                    print(f"Response time of {obj.component_id} is {obj.response_times[-1]}")
                if type(obj) is Task:
                    print(f"Response time of {obj.task_name} is {obj.response_times[-1]}")
                obj.current_execution = 0
                obj.current_start_time = 0
                return True
            return False

        assert self.cores != None and len(self.cores) > 0, "No cores found"
        print("Simulating...")
        # Initialize the ready queue for each core
        # for each component in the ready queue inizialize the ready queue of tasks
        for core in self.cores:
           core.components = schedule_object(core.scheduler, core.components)
           for component in core.components:
               component.tasks = schedule_object(component.scheduler, component.tasks)

        current_time = 0
        while current_time < self.simulation_time:
            print(f"Current time: {current_time}")
            for core in self.cores:
                core.ready_queue += [t for t in core.components if current_time % t.period == 0]
                if len(core.ready_queue) > 0:
                    component: Component = schedule_object(core.scheduler, core.ready_queue)[0]
                    # if we have a component to execute we go ahead and update the values
                    # if the component has not started we set the start time
                    check_if_started(component, current_time)
                    # get the ready queue of the tasks
                    component.ready_queue += [t for t in component.tasks if current_time % t.period == 0]
                    if len(component.ready_queue) > 0:
                        current_task: Component = schedule_object(component.scheduler, component.ready_queue)[0]
                        check_if_started(current_task, current_time)
                        if check_if_ended(current_task, current_time):
                            component.ready_queue.remove(current_task)
                        current_task.current_execution += 1
                    # if we have reached the end of the component we keep the response time
                    # and reset the execution time
                    # increase the execution time by one
                    if check_if_ended(component, current_time):
                        core.ready_queue.remove(component)
                    component.current_execution += 1
            current_time += self.advance_time(current_time)

        for core in self.cores:
            for component in core.components:
                print(component.response_times)
                for task in component.tasks:
                    print(task.response_times)

    def advance_time(self, current_time: int) -> int:
        next_time = []
        for core in self.cores:
            if len(core.ready_queue) < 1:
                next_time.append(int(min([c.period - (current_time % c.period) for c in core.components])))
            else:
                for component in core.components:
                    if len(component.ready_queue) < 1:
                        next_time.append(int(min([c.period - (current_time % c.period) for c in component.tasks])))
                    else:
                        return 1
        print("Next time: ",next_time)
        return min(next_time)
