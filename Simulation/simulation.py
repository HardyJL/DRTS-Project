from models.architecture import Architecture
from models.budgets import Budgets
from models.solution import Solution
from models.task import Task
import csvs.csv_functions
import os.path


def simulation(test_folder:str,max_cycles:int):
    #Use csv_function to initialize architecture, budgets and task
    architecture, budgets, tasks=csvs.csv_functions.load_models_from_csv(test_folder)
    # print(architecture)
    # print(budgets)
    # print(tasks)
    current_cycle = 0 

    core_assignment={}
    for i in architecture:
        core_assignment[i.core_id] = {} 
    for i in budgets:
        core_assignment[i.core_id][i.component_id] = []
        for j in tasks:
            if j.component_ID==i.component_id:
                core_assignment[i.core_id][i.component_id].append(j)
    print(core_assignment)



    while current_cycle <= max_cycles:


        break