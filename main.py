import sys
import os.path

from csv_functions import load_models_from_csv
from models import Task, Core, Component
from simulation import Simulation


def load_models(architectures, tasks, budgets):
    cores, tasks, components = load_models_from_csv(architectures, Core), load_models_from_csv(
        tasks, Task), load_models_from_csv(budgets, Component)

    assert len(cores) > 0 and len(tasks) > 0 and len(
        components) > 0, "No cores, tasks or components found in the csv files"

    for component in components:
        component.tasks = [
            task for task in tasks if task.component_id == component.component_id]

    for core in cores:
        core.components = [
            component for component in components if component.core_id == core.core_id]

    return cores


def main():
    # check if the user has provided the path to the test folder
    assert len(sys.argv) == 3 and sys.argv[1] != "" and sys.argv[1] != None
    # check if the expected path is correct
    expected_path = os.path.join(os.getcwd(), sys.argv[1])
    assert os.path.exists(
        expected_path), f"Path {expected_path} does not exist"

    architectures, tasks, budgets = expected_path + \
        "/architecture.csv", expected_path + "/tasks.csv", expected_path + "/budgets.csv"
    assert os.path.exists(architectures) and os.path.exists(tasks) and os.path.exists(
        budgets), f"Path {architectures} or {tasks} or {budgets} does not exist"

    cores = load_models(architectures, tasks, budgets)

    simulator = Simulation(cores)
    simulator.simulate(str(sys.argv[1]))
    # simulator.simulate(int(sys.argv[2]),str(sys.argv[1]))

def main_test(test_folder):
    # This function is for testing purposes only
    architectures, tasks, budgets = f"{test_folder}/architecture.csv", f"{test_folder}/tasks.csv", f"{test_folder}/budgets.csv"
    cores = load_models(architectures, tasks, budgets)

    simulator = Simulation(cores)
    simulator.simulate(test_folder)
    # simulator.simulate(int(sys.argv[2]),str(sys.argv[1]))


if __name__ == "__main__":
    # main()

    # Iterate over all test folders in the test directory
    test_directory = "Test-Cases"

    for root, dirs, files in os.walk(test_directory):
        for dirname in dirs:
            test_folder = os.path.join(root, dirname)
            main_test(test_folder)
