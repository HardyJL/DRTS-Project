import csv
from typing import List, Any, Type # Ensure Type is imported

# Assuming your model classes (Task, Component, Core, Solution) are defined
# in analysis.core or are imported appropriately.
# from .core import Task, Component, Core, Solution # Example if they are in core.py

# T = TypeVar('T') # Not strictly needed if using Type[Any] or specific types

def load_csv_data(file_path: str, model_class: Type[Any]) -> List[Any]: # Use Type[Any] for generic model_class
    """
    Load data from a CSV file into model objects.
    
    Args:
        file_path: Path to the CSV file
        model_class: Class to instantiate for each row (e.g., Task, Component)
        
    Returns:
        List of model instances
    """
    models = []
    
    try:
        with open(file_path, 'r', newline='') as csvfile: # Added newline=''
            reader = csv.DictReader(csvfile)
            for i, row in enumerate(reader):
                # Sanitize row keys: remove leading/trailing whitespace
                # and handle potential byte order mark (BOM) in the first header
                # This is especially important if CSVs are saved with BOM from some editors
                
                # Get headers from the reader if it's the first row, to handle BOM in first key
                # if i == 0:
                #     fieldnames = [key.lstrip('\ufeff') for key in reader.fieldnames]
                # else:
                #     fieldnames = reader.fieldnames

                # cleaned_row = {key.strip(): value for key, value in row.items()}
                # A more robust way to clean keys, especially the first one for BOM:
                cleaned_row = {}
                for k, v in row.items():
                    # Remove BOM from the first key if present
                    new_key = k.lstrip('\ufeff').strip()
                    cleaned_row[new_key] = v

                try:
                    # Ensure all expected arguments for the model_class constructor are present in cleaned_row,
                    # or that the constructor handles missing ones with defaults.
                    # For example, if Task expects 'task_type', it should be in the CSV or handled by default.
                    model = model_class(**cleaned_row)
                    models.append(model)
                except TypeError as te:
                    print(f"TypeError creating {model_class.__name__} from row {i+1} ({row}): {te}")
                    print(f"  Ensure constructor of {model_class.__name__} matches CSV columns or has defaults for missing ones.")
                    print(f"  CSV Headers: {reader.fieldnames}")
                    print(f"  Row Data Processed: {cleaned_row}")
                except Exception as e:
                    print(f"Error creating {model_class.__name__} from row {i+1} ({row}): {e}")
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return [] # Return empty list or raise error
    except Exception as e:
        print(f"An unexpected error occurred while reading {file_path}: {e}")
        return [] # Return empty list or raise error
            
    return models

# Example of your other functions (ensure Solution class is defined as above)
def write_solutions_to_csv(solutions: List[Any], filename_prefix: str) -> None: # Assuming Solution type
    output_filename = f"{filename_prefix}_solutions.csv"
    if not solutions:
        print(f"Warning: No solutions to write for {output_filename}")
        return
    try:
        with open(output_filename, mode='w', newline='') as csvfile:
            # Use the header method from the Solution object if it exists
            if hasattr(solutions[0], 'header') and callable(solutions[0].header):
                writer = csv.DictWriter(csvfile, fieldnames=solutions[0].header())
                writer.writeheader()
                for solution in solutions:
                     # Assuming solution objects can be converted to dicts or have attributes matching headers
                     writer.writerow(solution.__dict__) # Simple way if attributes match header
            else: # Fallback if no header method
                # This part might need adjustment based on how Solution objects are structured
                # For DictWriter, it expects dictionaries.
                print("Warning: Solution objects do not have a .header() method. CSV writing might be incomplete.")
                # Example: if solution is a simple list/tuple matching a predefined header
                # fieldnames_manual = ['task_name', 'component_id', 'task_schedulable', 'avg_response_time', 'max_response_time', 'component_schedulable']
                # writer = csv.writer(csvfile)
                # writer.writerow(fieldnames_manual)
                # for sol_data in solutions: writer.writerow(sol_data)


    except Exception as e:
        print(f"Error writing to CSV file {output_filename}: {e}")

# lcm_of_list can remain as is
import math
from functools import reduce
def lcm_of_list(numbers: List[int]) -> int:
    """Calculate the least common multiple of a list of numbers."""
    if not numbers:
        return 1 # LCM of empty set is 1
    
    # Filter out any non-positive numbers if necessary, or ensure inputs are positive
    positive_numbers = [n for n in numbers if n > 0]
    if not positive_numbers:
        if any(n == 0 for n in numbers): # LCM with 0 is 0
            return 0
        return 1 # Or handle as an error if all numbers are negative/non-positive

    def lcm(a: int, b: int) -> int:
        if a == 0 or b == 0:
            return 0
        return abs(a * b) // math.gcd(a, b) if a != 0 and b != 0 else 0
    
    return reduce(lcm, positive_numbers) if positive_numbers else 1