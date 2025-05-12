import csv
from typing import List, Any, Type # Ensure Type is imported


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
