import sys
import os.path

from csv_functions import load_models_from_csv
from models import Task, Core, Component
from scheduler import earliest_deadline_first, fixed_priority_with_rm

def load_models(architectures, tasks, budgets):
    cores = load_models_from_csv(architectures, Core)
    tasks = load_models_from_csv(tasks, Task)
    components = load_models_from_csv(budgets, Component)

    assert len(cores) > 0 and len(tasks) > 0 and len(components) > 0 

    for component in components:
        component.core = [core for core in cores if core.core_id == component.core_id][0]
        if component.scheduler == 'EDF':
            print("Using EDF scheduler")
            component.tasks = earliest_deadline_first([task for task in tasks if task.component_ID == component.component_id])
        elif component.scheduler == 'RM':
            print("Using RM scheduler")
            component.tasks = fixed_priority_with_rm([task for task in tasks if task.component_ID == component.component_id])
        else:
            print(component.scheduler)
            sys.exit()
    return components 



def main():
    # check if the user has provided the path to the test folder
    assert len(sys.argv) == 2 and sys.argv[1] != "" and sys.argv[1] != None
    # check if the expected path is correct
    expected_path = os.path.join(os.getcwd(), sys.argv[1])
    assert os.path.exists(expected_path)

    architectures, tasks, budgets = expected_path + "/architecture.csv", expected_path + "/tasks.csv", expected_path + "/budgets.csv"
    assert os.path.exists(architectures) and os.path.exists(tasks) and os.path.exists(budgets)

    components = load_models(architectures, tasks, budgets) 
    print("Components: ", components)


if __name__ == "__main__":
    main()
