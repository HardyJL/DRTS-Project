#!/usr/bin/env python3
"""
Example script demonstrating how to use the hierarchical taskset generator
to create a suite of test cases with different characteristics.
"""

import os
import sys
import random

# Add parent directory to path to import generator package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hierarchical_generator.config import Config
from hierarchical_generator.core_generator import CoreGenerator
from hierarchical_generator.component_generator import ComponentGenerator
from hierarchical_generator.task_generator import TaskGenerator
from hierarchical_generator.writer import CSVWriter


def generate_test_case(name, num_cores, num_components, num_tasks, 
                      utilization, schedulable=True, speed_range=(0.5, 1.5), seed=None):
    """Generate a single test case with the given parameters."""
    # Set up configuration
    config = Config()
    config.num_cores = num_cores
    config.num_components = num_components
    config.num_tasks = num_tasks
    config.utilization = utilization
    config.output_dir = "Generated_Test_Cases"
    config.test_case_name = name
    config.speed_factor_range = speed_range
    config.schedulable = schedulable
    config.seed = seed
    
    # Set random seed if provided
    if seed is not None:
        random.seed(seed)
    
    # Initialize generators
    core_generator = CoreGenerator(config)
    component_generator = ComponentGenerator(config)
    task_generator = TaskGenerator(config)
    csv_writer = CSVWriter(config)
    
    # Generate cores
    cores = core_generator.generate_cores()
    
    # Distribute utilization among cores
    core_utils = core_generator.distribute_utilization(utilization / 100.0, cores)
    
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
    
    print(f"Generated test case: {name}")


def main():
    """Generate a suite of test cases with different characteristics."""
    # Create output directory if it doesn't exist
    os.makedirs("Test_Cases", exist_ok=True)
    
    # Test case 1: Small system (few cores, components, tasks)
    generate_test_case(
        name="small-test-case",
        num_cores=2,
        num_components=4,
        num_tasks=8,
        utilization=60,
        schedulable=True,
        seed=42
    )
    
    # Test case 2: Medium system
    generate_test_case(
        name="medium-test-case",
        num_cores=4,
        num_components=8,
        num_tasks=20,
        utilization=70,
        schedulable=True,
        seed=43
    )
    
    # Test case 3: Large system (many cores, components, tasks)
    generate_test_case(
        name="large-test-case",
        num_cores=8,
        num_components=8,
        num_tasks=40,
        utilization=75,
        schedulable=True,
        seed=44
    )
    
    # Test case 4: High utilization system
    generate_test_case(
        name="high-util-test-case",
        num_cores=4,
        num_components=8,
        num_tasks=20,
        utilization=85,
        schedulable=True,
        seed=45
    )
    
    # Test case 5: Unschedulable system
    generate_test_case(
        name="unschedulable-test-case",
        num_cores=4,
        num_components=8,
        num_tasks=20,
        utilization=70,
        schedulable=False,
        seed=46
    )
    
    # Test case 6: Wide range of core speeds
    generate_test_case(
        name="varied-speeds-test-case",
        num_cores=4,
        num_components=8,
        num_tasks=20,
        utilization=70,
        schedulable=True,
        speed_range=(0.2, 2.0),
        seed=47
    )
    
    print("\nAll test cases generated successfully!")


if __name__ == "__main__":
    main()