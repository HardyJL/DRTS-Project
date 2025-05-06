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
        
        Args:
            config: Configuration object with settings
        """
        self.config = config
    
    def write_csv_files(self, cores: List[Dict[str, Any]], 
                        components: List[Dict[str, Any]], 
                        tasks: List[Dict[str, Any]]) -> None:
        """
        Write the generated data to CSV files.
        
        Args:
            cores: List of core dictionaries
            components: List of component dictionaries
            tasks: List of task dictionaries
        """
        # Create the output directory if it doesn't exist
        full_output_dir = os.path.join(self.config.output_dir, self.config.test_case_name)
        os.makedirs(full_output_dir, exist_ok=True)
        
        # Write architecture.csv
        with open(os.path.join(full_output_dir, "architecture.csv"), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["core_id", "speed_factor", "scheduler"])
            for core in cores:
                writer.writerow([core["core_id"], core["speed_factor"], core["scheduler"]])
        
        # Write budgets.csv
        with open(os.path.join(full_output_dir, "budgets.csv"), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["component_id", "scheduler", "budget", "period", "core_id", "priority"])
            for comp in components:
                # Remove utilization - it's not part of the actual format
                comp_data = comp.copy()
                if "utilization" in comp_data:
                    del comp_data["utilization"]
                writer.writerow([
                    comp_data["component_id"], 
                    comp_data["scheduler"], 
                    comp_data["budget"], 
                    comp_data["period"], 
                    comp_data["core_id"], 
                    comp_data["priority"]
                ])
        
        # Write tasks.csv
        with open(os.path.join(full_output_dir, "tasks.csv"), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["task_name", "wcet", "period", "component_id", "priority"])
            for task in tasks:
                writer.writerow([
                    task["task_name"], 
                    task["wcet"], 
                    task["period"], 
                    task["component_id"], 
                    task["priority"]
                ])
        
        print(f"Generated files written to {full_output_dir}")
        