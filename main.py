import sys
import os.path

from simulation import Simulation
from csv_functions import load_models_from_csv
from models import Task, Core, Component

def main():
    #Check if folders exist
    # if not os.path.exists(os.path.join(os.getcwd(), sys.argv[1])):
    #     print("Test folder doesnt exist")
    #     sys.exit()
    architectures = os.path.join(os.getcwd(), sys.argv[1], "architecture.csv")
    tasks = os.path.join(os.getcwd(), sys.argv[1], "tasks.csv")
    budgets = os.path.join(os.getcwd(), sys.argv[1], "budgets.csv")

    if not os.path.exists(architectures):
        print("Architecture file does not exist")
        sys.exit()
    if not os.path.exists(tasks):
        print("Tasks file does not exist")
        sys.exit()
    if not os.path.exists(budgets):
        print("Budgets file does not exist")
        sys.exit()

    cores = load_models_from_csv(architectures, Core)
    tasks = load_models_from_csv(tasks, Task)
    componets = load_models_from_csv(budgets, Component)

    for component in componets:
        component.core = [core for core in cores if core.core_id == component.core_id][0]
        component.tasks = [task for task in tasks if task.component_ID == component.component_id]
        
    
    print("Components: ", componets)


if __name__ == "__main__":
    main()
