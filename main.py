from models import Task


if __name__ == "__main__":
    task = Task(task_id= "Test", wcet=1, deadline=1, core_assignment="core1")
    print(task)
