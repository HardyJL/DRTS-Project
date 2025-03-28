import csv

def load_models_from_csv(filename) -> list:
    models = []
    try:
        with open(filename, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header
            for row in reader:
                models.append(*row)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
