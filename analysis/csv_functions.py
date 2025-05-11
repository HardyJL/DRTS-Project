import os
import sys
import csv
import math
from typing import List, Dict, Tuple, Optional, Union, Any
from functools import reduce
from bdr_model import BDRModel
from core import Core, Component, Task, Solution
from typing import TypeVar, List, Type
# from models import Solution

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


def lcm_of_list(numbers: List[int]) -> int:
    """Calculate the least common multiple of a list of numbers."""
    def lcm(a: int, b: int) -> int:
        return abs(a * b) // math.gcd(a, b)
    
    return reduce(lcm, numbers, 1)


def load_csv_data(file_path: str, model_class) -> List[Any]:
    """
    Load data from a CSV file into model objects.
    
    Args:
        file_path: Path to the CSV file
        model_class: Class to instantiate for each row
        
    Returns:
        List of model instances
    """
    models = []
    
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Create a model instance from the row data
            try:
                model = model_class(**row)
                models.append(model)
            except Exception as e:
                print(f"Error creating {model_class.__name__} from row {row}: {e}")
    
    return models