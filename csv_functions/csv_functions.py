import csv

from typing import TypeVar, List, Type
from models import Solution

T = TypeVar('T')

def load_models_from_csv(filename: str, model_type: Type[T]) -> List[T]:
     models = []
     try:
         with open(filename, newline='') as csvfile:
             reader = csv.reader(csvfile)
             next(reader)  # Skip header
             for row in reader:
                models.append(model_type(*row))
     except Exception as e:
         print(f"Error reading CSV file: {e}")
         exit(1)
     return models

def write_solutions_to_csv(solutions: List[Solution], filename) -> None:
    filename= ""+filename+"_solutions.csv"
    try:
        with open(filename, mode='w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Write the header
            writer.writerow(solutions[0].header())
            # Write the solution rows
            for solution in solutions:
                writer.writerow([solution.task_name, solution.component_id, solution.task_schedulable, 
                                 solution.avg_response_time, solution.max_response_time, solution.component_schedulable])
    except Exception as e:
        print(f"Error writing to CSV file: {e}")
        exit(1)