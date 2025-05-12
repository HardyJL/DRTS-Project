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
        self.sporadic_task_ratio = 0.0
        self.sporadic_deadline_factor_range = (0.7, 1.0)

        # New configurations for server parameters
        self.server_period_range = (20, 100)  # Example: Server periods between 20 and 100
        self.server_budget_factor_range = (0.1, 0.3) # Server budget as 10-30% of server period
                                                    # This implies server utilization of 0.1 to 0.3


    @staticmethod
    def parse_arguments() -> 'Config':
        """Parse command line arguments and return a Config object"""
        parser = argparse.ArgumentParser(description='Generate hierarchical tasksets')
        # ... (keep existing arguments) ...
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
        parser.add_argument('--sporadic-ratio', type=float, default=0.0,
                            help='Ratio of sporadic tasks (0.0 to 1.0)')
        parser.add_argument('--sporadic-deadline-range', type=str, default='0.7,1.0',
                            help='Range for sporadic task deadline factor relative to MIT (MIN_FACTOR,MAX_FACTOR)')

        # New arguments for server parameters
        parser.add_argument('--server-period-range', type=str, default='20,100',
                            help='Range for server periods (MIN_PERIOD,MAX_PERIOD)')
        parser.add_argument('--server-budget-factor-range', type=str, default='0.1,0.3',
                            help='Range for server budget factor relative to server period (MIN_FACTOR,MAX_FACTOR)')

        args = parser.parse_args()

        config = Config()
        config.num_cores = args.num_cores
        config.num_components = args.num_components
        config.num_tasks = args.num_tasks
        config.utilization = args.utilization
        config.output_dir = args.output_dir
        config.test_case_name = args.test_case_name

        speed_min, speed_max = map(float, args.speed_factor_range.split(','))
        config.speed_factor_range = (speed_min, speed_max)

        config.schedulable = not args.unschedulable
        config.seed = args.seed
        config.sporadic_task_ratio = max(0.0, min(1.0, args.sporadic_ratio))

        try:
            deadline_min_factor, deadline_max_factor = map(float, args.sporadic_deadline_range.split(','))
            if 0 < deadline_min_factor <= deadline_max_factor:
                config.sporadic_deadline_factor_range = (deadline_min_factor, deadline_max_factor)
            else:
                print(f"Warning: Invalid sporadic-deadline-range '{args.sporadic_deadline_range}'. Using default {config.sporadic_deadline_factor_range}.")
        except ValueError:
            print(f"Warning: Could not parse sporadic-deadline-range '{args.sporadic_deadline_range}'. Using default {config.sporadic_deadline_factor_range}.")

        try:
            s_period_min, s_period_max = map(int, args.server_period_range.split(','))
            if 0 < s_period_min <= s_period_max:
                config.server_period_range = (s_period_min, s_period_max)
            else:
                print(f"Warning: Invalid server-period-range '{args.server_period_range}'. Using default {config.server_period_range}.")
        except ValueError:
            print(f"Warning: Could not parse server-period-range '{args.server_period_range}'. Using default {config.server_period_range}.")

        try:
            s_budget_min_f, s_budget_max_f = map(float, args.server_budget_factor_range.split(','))
            if 0 < s_budget_min_f <= s_budget_max_f <= 1.0: # Budget factor should be <= 1
                config.server_budget_factor_range = (s_budget_min_f, s_budget_max_f)
            else:
                print(f"Warning: Invalid server-budget-factor-range '{args.server_budget_factor_range}'. Using default {config.server_budget_factor_range}.")
        except ValueError:
            print(f"Warning: Could not parse server-budget-factor-range '{args.server_budget_factor_range}'. Using default {config.server_budget_factor_range}.")


        config.print_config()
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
            ['Seed', self.seed if self.seed is not None else 'None'],
            ['Sporadic Task Ratio', f'{self.sporadic_task_ratio:.2f}'],
            ['Sporadic Deadline Factor Range (rel. to MIT)', f'{self.sporadic_deadline_factor_range[0]:.2f} - {self.sporadic_deadline_factor_range[1]:.2f}'],
            # New server param print
            ['Server Period Range', f'{self.server_period_range[0]} - {self.server_period_range[1]}'],
            ['Server Budget Factor Range (rel. to Period)', f'{self.server_budget_factor_range[0]:.2f} - {self.server_budget_factor_range[1]:.2f}']
        ]

        print(tabulate.tabulate(config_data, headers=['Parameter', 'Value'], tablefmt='grid'))
        print("\nConfiguration settings loaded successfully.")