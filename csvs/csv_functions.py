import csv
import os.path

def load_models_from_csv(folder_name:str)-> tuple:
    models = []
    path=os.path.join(folder_name)
    return load_architecture_from_csv(path+"/architecture.csv"),load_budgets_from_csv(),load_task_from_csv()
    # try:
    #     with open(filename, newline='') as csvfile:
    #         reader = csv.reader(csvfile)
    #         next(reader)  # Skip header
    #         for row in reader:
    #             models.append(*row)
    #         return models
    # except Exception as e:
    #     print(f"Error reading CSV file: {e}")

def load_architecture_from_csv(file):
    print(os.path.exists(file))
    print(file)
    return
def load_budgets_from_csv():
    return
def load_task_from_csv():
    return


def write_solution_to_csv(models, filename) -> None:
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(models[0].header())
            for model in models:
                writer.writerow(model.__iter__())
    except Exception as e:
        print(f"Error reading CSV file: {e}")
