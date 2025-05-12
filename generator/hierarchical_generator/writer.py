"""
CSV writer module for hierarchical taskset generator
"""
import os
import csv
from typing import List, Dict, Any


class CSVWriter:
    """Writer for taskset CSV files"""

    def __init__(self, config):
        """
        Initialize the CSV writer
        """
        self.config = config

    def write_csv_files(self, cores: List[Dict[str, Any]],
                        components: List[Dict[str, Any]],
                        tasks: List[Dict[str, Any]]) -> None:
        """
        Write the generated data to CSV files.
        """
        full_output_dir = os.path.join(self.config.output_dir, self.config.test_case_name)
        os.makedirs(full_output_dir, exist_ok=True)

        # Write architecture.csv
        with open(os.path.join(full_output_dir, "architecture.csv"), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["core_id", "speed_factor", "scheduler"])
            for core in cores:
                writer.writerow([core["core_id"], core["speed_factor"], core["scheduler"]])

        # Write budgets.csv
        budgets_csv_path = os.path.join(full_output_dir, "budgets.csv")
        with open(budgets_csv_path, 'w', newline='') as f:
            # Add 'server_budget' and 'server_period' to the header
            fieldnames = ["component_id", "scheduler", "budget", "period", "core_id", "priority", "server_budget", "server_period"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for comp in components:
                row_data = {
                    "component_id": comp.get("component_id"),
                    "scheduler": comp.get("scheduler"),
                    "budget": comp.get("budget"),
                    "period": comp.get("period"),
                    "core_id": comp.get("core_id"),
                    "priority": comp.get("priority", ""),
                    # Get server params, default to empty string if not present or not relevant
                    "server_budget": comp.get("server_budget", ""),
                    "server_period": comp.get("server_period", "")
                }
                # If sporadic_task_ratio is 0, we might not want to write server params
                # or let them be empty as default.
                # The current component_generator always adds them if the ratio > 0
                # We can refine to write "" if num_sporadic_tasks for this comp was 0.
                # For now, it writes the generated values.
                
                # Check if this component actually has sporadic tasks assigned to it
                has_sporadic_tasks = any(
                    task.get("component_id") == comp.get("component_id") and task.get("task_type") == "sporadic"
                    for task in tasks
                )
                if not has_sporadic_tasks:
                    row_data["server_budget"] = ""
                    row_data["server_period"] = ""
                    
                writer.writerow(row_data)
        print(f"Budgets CSV includes 'server_budget' and 'server_period': {budgets_csv_path}")


        # Write tasks.csv
        tasks_csv_path = os.path.join(full_output_dir, "tasks.csv")
        with open(tasks_csv_path, 'w', newline='') as f:
            fieldnames = ["task_name", "wcet", "period", "component_id", "priority", "task_type", "deadline"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for task in tasks:
                row_data = {
                    "task_name": task.get("task_name"), "wcet": task.get("wcet"),
                    "period": task.get("period"), "component_id": task.get("component_id"),
                    "priority": task.get("priority", ""), "task_type": task.get("task_type", "periodic"),
                    "deadline": task.get("deadline", task.get("period"))
                }
                writer.writerow(row_data)
        print(f"Tasks CSV includes 'task_type' and 'deadline': {tasks_csv_path}")

        print(f"\nGenerated files written to {full_output_dir}")