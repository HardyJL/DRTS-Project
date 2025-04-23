import csv
import os.path
from models.core import Core
from models.component import Component
from models.task import Task
def load_models_from_csv(folder_name:str)-> tuple[list[Core], list[Component], list[Task]]:
    models = []
    path=os.path.join(folder_name)
    return load_architecture_from_csv(path+"/architecture.csv"),load_budgets_from_csv(path+"/budgets.csv"),load_task_from_csv(path+"/tasks.csv")


def load_architecture_from_csv(file):
    print(os.path.exists(file))
    print(file)
    try:
        architecture=[]
        with open(file, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header
            for row in reader:
                architecture.append(Core((row[0]), (row[1]), row[2]))
            #print(architecture)    
            return architecture
    except Exception as e:
        print(f"Error reading CSV architecture file: {e}")
def load_budgets_from_csv(file):
    try:
        budgets=[]
        with open(file, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header
            for row in reader:
                budgets.append(Component((row[0]), (row[1]), row[2], row[3], row[4]))
            #print(budgets)    
            return budgets
    except Exception as e:
        print(f"Error reading CSV budgets file: {e}")
def load_task_from_csv(file):
    try:
        tasks=[]
        with open(file, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header
            for row in reader:
                tasks.append(Task((row[0]), (row[1]), row[2], row[3], row[4]))
            #print(tasks)    
            return (tasks)
    except Exception as e:
        print(f"Error reading CSV task file: {e}")
    return


def write_solution_to_csv(models, filename) -> None:
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(models[0].header())
            for model in models:
                writer.writerow(model.__iter__())
    except Exception as e:
        print(f"Error reading CSV writer file: {e}")
