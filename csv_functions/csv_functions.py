import csv

from typing import TypeVar, List, Type

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
