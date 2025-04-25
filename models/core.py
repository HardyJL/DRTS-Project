class Core: 
    def __init__(self, core_id, speed_factor,scheduler):
        self.core_id = core_id
        self.speed_factor = float(speed_factor)
        self.scheduler = scheduler

        self.components: dict[str, 'Budgets'] = {} # Holds assigned components {component_id: component_obj}
        # Add any core-level runtime state if needed (e.g., currently running component)
        self.running_component_id: str | None = None
    
    def assign_component(self, component: 'Budgets'):

        
        """Assigns a component to this core."""
        if component.core_id == self.core_id:
            self.components[component.component_id] = component
        else:
            print(f"Warning: Component {component.component_id} core_id mismatch for Core {self.core_id}")



    def get_eligible_components(self) -> list['Budgets']:

        """Returns components on this core ready to run (have budget & ready tasks)."""

        eligible = []
        for comp in self.components.values():
            # Check budget and if there's anything waiting/running in the component
            if comp.current_budget > 0 and (comp.running_job or comp.ready_queue):
                 eligible.append(comp)
        return eligible   
    
    
    def __repr__(self) -> str:
        return f"\nCore ID = ({self.core_id}) | Seed factor ({self.speed_factor}) | Scheduler ({self.scheduler})" 

