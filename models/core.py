from .component import Component


class Core:
    def __init__(self, core_id, speed_factor, scheduler=None):
        self.core_id = core_id
        self.speed_factor = float(speed_factor)
        self.scheduler = scheduler
        self.components: list[Component] = []
        self.ready_queue: list[Component] = []
        self.execution_time = 0.0

    def __repr__(self) -> str:
        return f"\nCore ID = ({self.core_id}) | Seed factor ({self.speed_factor}) | Scheduler ({self.scheduler}) \n Components ({self.components})"

    def finish_component(self, component: Component, time_difference: int) -> None:
        """Finishes the given component and reduces the
        remaining time of the task and components to the correct values.
        Args:
            component (Component): Component to finish
            time_difference (int): the time difference between the current time and the time of the finish
        """
        if len(component.ready_queue) > 0:
            component.ready_queue[0].remaining_time = time_difference
        component.remaining_time = component.budget
        self.ready_queue.remove(component)

    def raise_component(self, components_to_raise: list[Component], time_difference: int) -> None:
        """ Raises all given components and reduces 
        the remaining time of the task and components 
        to the correct values.
        Args:
            components_to_raise (list[Component]): The components to raise
            time_difference (int): the time difference between the current time and the time of the raise 
        """
        if len(self.ready_queue) > 0:
            active_component = self.ready_queue[0]
            active_component.remaining_time -= time_difference
            if len(active_component.ready_queue) > 0:
                active_component.ready_queue[0].remaining_time = time_difference
        for component in components_to_raise:
            self.ready_queue.append(component)
