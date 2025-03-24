import csv

from ..models import Task, Solution

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

