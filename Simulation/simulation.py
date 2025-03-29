from models.architecture import Architecture
from models.budgets import Budgets
from models.solution import Solution
from models.task import Task
import csvs.csv_functions
import os.path


def simulation(test_folder:str,max_cycles:int):
    #Use csv_function to initialize architecture, budgets and task
    architecture, budgets, tasks=csvs.csv_functions.load_models_from_csv(test_folder)
    print(architecture)
    print(budgets)
    print(tasks)
    #architecture= 