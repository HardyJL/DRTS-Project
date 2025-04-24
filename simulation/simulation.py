from models import Core, Component 

class Simulation:
    def simulate(self, cores: list[Core], simulation_time: int):
        def schedule_object(scheduler, object_list):
           if scheduler == "EDF":
               return sorted(object_list, key= lambda obj: obj.period)
           elif scheduler == "RM":
               return sorted(object_list, key= lambda obj: obj.priority)
           else:
               raise ValueError(scheduler)
        print("Simulating...")
        # Set up a ready queue for each core this
        # Based on the algrithm of the core make sure to ready queu is the correct component
        # then for the component create a ready queue with the task
        for core in cores:
           core.components = schedule_object(core.scheduler, core.components)
           for component in core.components:
               component.tasks = schedule_object(component.scheduler, component.tasks)

        current_time = 0
        while current_time < simulation_time:
            for core in cores:
                core.ready_queue += [t for t in core.components if current_time % t.period == 0]
                current_component: Component = schedule_object(core.scheduler, core.ready_queue)[0]
                if current_component:
                    print(f"{current_component.component_id} - {current_component.current_execution} - {current_time}")
                    current_component.current_execution += 1
                    if (current_component.current_execution >= current_component.budget):
                        current_component.current_execution = 0
                        core.ready_queue.remove(current_component)
                        
            current_time += self.advance_time(current_time= current_time, ready_queue= core.ready_queue, components= core.components)


    def advance_time(self,current_time, ready_queue, components: list[Component]) -> int:
        if len(ready_queue) < 1:
            remainder = min([c.period - (current_time % c.period) for c in components])
            return int(remainder)
        return 1
