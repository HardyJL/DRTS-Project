import csv

from . import Task

def load_tasks_from_csv(filename) -> list[Task]:
    """
    Loads tasks from csv file

    Args:
        filename string: path to csv file

    Returns:
        List of tasks
    """
    tasks = []
    try:
        with open(filename, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header
            for row in reader:
                tasks.append(Task(*row))
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        exit(1)
    return tasks

def create_csv_file(filename) -> None:
    try:
        with open(filename, newline='') as csvfile:
            writer = csv.writer(csvfile)
            
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        exit(1)
