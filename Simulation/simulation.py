from models.core import Core
from models.component import Component
from models.solution import Solution
from models.task import Task
from models.job import Job
import csvs.csv_functions
import os.path
from scheduler import Scheduler


def simulation(test_folder:str,max_cycles:int):
    print("Starting the simulation...\n--------------------------------------------------")
    print("Fetching Data...\n--------------------------------------------------")

    cores, components, tasks=csvs.csv_functions.load_models_from_csv(test_folder)
    print("Creating Dictionaries...\n--------------------------------------------------")

    cores_dict: dict[str, Core] = {core.core_id: core for core in cores} # Assuming architecture is list[Core]
    components_dict: dict[str, Component] = {comp.component_id: comp for comp in components} # Assuming budgets is list[Component]
    tasks_list: list[Task] = tasks # Assuming tasks is list[Task]

    """
    Initializes the dictionary associating cores with componentes
    """
    for comp_id, comp_obj in components_dict.items():
        if comp_obj.core_id in cores_dict:
            cores_dict[comp_obj.core_id].assign_component(comp_obj)
        else:
            print(f"Error: Core {comp_obj.core_id} not found for component {comp_id}")
    
    """
    Initializes the dictionary associating tasks with components
    """
    for task_obj in tasks_list:
        if task_obj.component_ID in components_dict:
            components_dict[task_obj.component_ID].assign_task(task_obj)
            # You might adjust task WCET here if needed, although better done at Job creation
        else:
            print(f"Error: Component {task_obj.component_ID} not found for task {task_obj.task_name}")

    
    
    """
    Initialize current state data for components
    """
    for comp in components_dict.values():
        print("i")
        comp.current_budget = comp.budget
        comp.budget_refresh_time = comp.period # First refresh at the end of the first period
        comp.ready_queue = []
        comp.running_job = None
    print("--- Initialized Cores ---")
    
    
    
 
    for core in cores_dict.values():
        print(core)
        for comp in core.components.values():
            print(comp) 
    
    current_cycle = 0
    """
    Print Statements showing initialized data
    """
    for core_id, core in cores_dict.items():
        for comp_id, component in core.components.items():
            for task_name, task in component.tasks.items():
                new_job = Job(task_ref=task, arrival_time=0, core_speed_factor=core.speed_factor)
                component.add_job_to_ready_queue(new_job)
                print(f"Initial Job Created: {new_job} for Component {comp_id}")
    
    while current_cycle <= max_cycles:
        print(f"\n--- Cycle {current_cycle} ---")
        # ... rest of simulation logic using cores_dict ...
        break # Placeholder



