#!/usr/bin/env python3
"""
Hierarchical Taskset Generator Main Script

This script generates realistic tasksets for hierarchical scheduling systems with
multiple cores, components, and tasks using EDF (Earliest Deadline First) and
RM (Rate Monotonic) scheduling algorithms.

Usage:
    python main.py [options]
"""

import random
import numpy as np
from hierarchical_generator.config import Config
from hierarchical_generator.core_generator import CoreGenerator
from hierarchical_generator.component_generator import ComponentGenerator
from hierarchical_generator.task_generator import TaskGenerator
from hierarchical_generator.writer import CSVWriter


def main():
    """Main function to generate hierarchical tasksets."""
    # Parse command line arguments
    config = Config.parse_arguments()
    
    # Set random seed if provided
    if config.seed is not None:
        random.seed(config.seed)
        np.random.seed(config.seed)
    
    # Print configuration
    config.print_config()
    
    # Convert utilization from percentage to fraction
    utilization = config.utilization / 100.0
    
    # Initialize generators
    core_generator = CoreGenerator(config)
    component_generator = ComponentGenerator(config)
    task_generator = TaskGenerator(config)
    csv_writer = CSVWriter(config)
    
    # Generate cores
    cores = core_generator.generate_cores()
    
    # Distribute utilization among cores
    core_utils = core_generator.distribute_utilization(utilization, cores)
    
    # Generate components
    components = component_generator.generate_components(cores, core_utils)
    
    # Distribute tasks among components
    tasks_per_component = task_generator.distribute_tasks(components)
    
    # Generate tasks
    tasks = task_generator.generate_tasks(components, tasks_per_component)
    
    # Adjust schedulability if needed
    tasks = component_generator.adjust_schedulability(components, tasks)
    
    # Write to CSV files
    csv_writer.write_csv_files(cores, components, tasks)
    
    print("Done!")


if __name__ == "__main__":
    main()