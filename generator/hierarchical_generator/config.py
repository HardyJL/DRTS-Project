"""
Configuration handling for the hierarchical generator.
This module provides a configuration class that loads and manages
configuration settings for the hierarchical generator.
"""

import argparse
from typing import Tuple, Optional
import tabulate


class Config:
    
    def __init__(self):

        self.num_cores = 4
        self.num_components = 8
        self.num_tasks = 20
        self.utilization = 70.0
        self.output_dir = 'Test_Cases/generated'
        self.test_case_name = 'hierarchical-test-case'
        self.speed_factor_range = (0.5, 1.5)
        self.schedulable = True
        self.seed = None

        self.print_config()

    @staticmethod
    def parse_arguments() -> 'Config':
        """Parse command line arguments and return a Config object"""
        parser = argparse.ArgumentParser(description='Generate hierarchical tasksets')
        parser.add_argument('--num-cores', type=int, default=4, 
                            help='Number of cores in the system')
        parser.add_argument('--num-components', type=int, default=8, 
                            help='Number of components across all cores')
        parser.add_argument('--num-tasks', type=int, default=20, 
                            help='Number of tasks across all components')
        parser.add_argument('--utilization', type=float, default=70.0, 
                            help='Total system utilization in percent')
        parser.add_argument('--output-dir', type=str, default='Test_Cases/generated', 
                            help='Directory to output the generated files')
        parser.add_argument('--test-case-name', type=str, default='hierarchical-test-case', 
                            help='Name of the test case')
        parser.add_argument('--speed-factor-range', type=str, default='0.5,1.5', 
                            help='Range for core speed factors (MIN,MAX)')
        parser.add_argument('--unschedulable', action='store_true', 
                            help='Generate an unschedulable system (default is schedulable)')
        parser.add_argument('--seed', type=int, default=None, 
                            help='Random seed for reproducibility')
        
        args = parser.parse_args()
        
        config = Config()
        config.num_cores = args.num_cores
        config.num_components = args.num_components
        config.num_tasks = args.num_tasks
        config.utilization = args.utilization
        config.output_dir = args.output_dir
        config.test_case_name = args.test_case_name
        
        # Parse speed factor range
        speed_min, speed_max = map(float, args.speed_factor_range.split(','))
        config.speed_factor_range = (speed_min, speed_max)
        
        config.schedulable = not args.unschedulable
        config.seed = args.seed
        
        return config
    

    def print_config(self):
        """Print the configuration settings in a tabular format"""
        config_data = [
            ['Number of Cores', self.num_cores],
            ['Number of Components', self.num_components],
            ['Number of Tasks', self.num_tasks],
            ['Total Utilization (%)', self.utilization],
            ['Output Directory', self.output_dir],
            ['Test Case Name', self.test_case_name],
            ['Speed Factor Range', f'{self.speed_factor_range[0]} - {self.speed_factor_range[1]}'],
            ['Schedulable', 'Yes' if self.schedulable else 'No'],
            ['Seed', self.seed if self.seed is not None else 'None']
        ]
        
        print(tabulate.tabulate(config_data, headers=['Parameter', 'Value'], tablefmt='grid'))
        print("\nConfiguration settings loaded successfully.")
        