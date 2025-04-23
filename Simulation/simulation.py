from models.architecture import Architecture
from models.budgets import Budgets
from models.solution import Solution
from models.task import Task
import csvs.csv_functions
import os.path
from scheduler import Scheduler


def simulation(test_folder:str,max_cycles:int):
    #Use csv_function to initialize architecture, budgets and task
    architecture, budgets, tasks=csvs.csv_functions.load_models_from_csv(test_folder)
    # print(architecture)
    # print(budgets)
    # print(tasks)
    current_cycle = 0 
    scheduler=Scheduler()
    core_assignment={}
    # for i in architecture:
    #     core_assignment[i.core_id] = (i,{}) 
    # for i in budgets:
    #     core_assignment[i.core_id][1][i.component_id] = (i,[])
    #     for j in tasks:
    #         if j.component_ID==i.component_id:
    #             core_assignment[i.core_id][1][i.component_id][1].append(j)
    # # print(core_assignment)
    # for i in core_assignment:
    #     for j in core_assignment[i][1]:
    #         if (core_assignment[i][1][j][0].scheduler)=="RM":
    #             print(core_assignment[i][1][j][1])
    #             core_assignment[i][1][j][1]=scheduler.rate_monotonic(core_assignment[i][1][j][1])
    #         elif (core_assignment[i][1][j][0].scheduler)=="EDF":
    #             core_assignment[i][1][j][1]=scheduler.earliest_deadline_first(core_assignment[i][1][j][1])


    print(core_assignment)



    while current_cycle <= max_cycles:


        break