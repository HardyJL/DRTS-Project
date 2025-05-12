
# Hierarchical Taskset Generator

A tool for generating synthetic tasksets for hierarchical scheduling systems with multiple cores, components, and tasks (both periodic and sporadic) using EDF (Earliest Deadline First) and RM (Rate Monotonic) scheduling algorithms. This implementation adapts some of the logic from https://github.com/porya-gohary/real-time-task-generators

## TODO List
1. Implement setup.py to make importable as a package

## Overview

This generator creates realistic test cases for evaluating hierarchical scheduling algorithms, particularly for systems like Advanced Driver-Assistance Systems (ADAS) running on multicore platforms. The generator produces:

* Cores with varying speed factors and schedulers (EDF/RM).
* Components assigned to cores, each with its own scheduler (inherited from the core), budget, and period defining its interface to the core scheduler. Components can also define internal server parameters (budget, period) for managing sporadic tasks.
* Tasks (periodic and sporadic) with execution times, periods (or Minimum Inter-arrival Times - MITs), and deadlines, assigned to components.

## Project Structure

The project follows an object-oriented design with the following structure:

```
generator/
├── __init__.py         # Package exports
├── config.py           # Configuration parameter handling
├── core_generator.py   # Core generation logic
├── component_generator.py # Component generation logic
├── task_generator.py   # Task (periodic & sporadic) generation logic
├── utils.py            # Utility functions
└── writer.py           # CSV file output handling

main.py                 # Entry point
examples/
└── generate_test_cases.py # Example script for generating multiple test cases
```

## Installation

Clone the repository and make sure you have the required dependencies:

```bash
# Clone the repository (replace with your actual URL if available)
# git clone [https://github.com/yourusername/hierarchical-taskset-generator.git](https://github.com/yourusername/hierarchical-taskset-generator.git)
# cd hierarchical-taskset-generator

# Install dependencies
pip install numpy tabulate
```
*(Note: `tabulate` is used for printing the configuration)*

## Usage

Run the generator with default parameters:

```bash
python main.py
```

Or customize the generation with command line arguments:

```bash
python main.py --num-cores=8 --num-components=16 --num-tasks=40 --utilization=80 --sporadic-ratio=0.2 --output-dir=MyTestCases --test-case-name=MySporadicTest
```

### Command Line Arguments

The configuration options can be set via command line arguments:

| Argument                        | Description                                                                 | Default                    |
| :------------------------------ | :-------------------------------------------------------------------------- | :------------------------- |
| `--num-cores`                   | Number of cores in the system                                               | 4                          |
| `--num-components`              | Number of components across all cores                                       | 8                          |
| `--num-tasks`                   | Total number of tasks (periodic + sporadic) across all components           | 20                         |
| `--utilization`                 | Target total system utilization in percent (distributed across cores)       | 70.0                       |
| `--output-dir`                  | Directory to output the generated files                                     | `Test_Cases/generated`     |
| `--test-case-name`              | Name of the test case (subdirectory within output-dir)                      | `hierarchical-test-case`   |
| `--speed-factor-range`          | Range for core speed factors (MIN,MAX)                                      | `0.5,1.5`                  |
| `--unschedulable`               | Generate a potentially unschedulable system (increases WCETs heuristically) | False (generates schedulable) |
| `--seed`                        | Random seed for reproducibility                                             | None                       |
| `--sporadic-ratio`              | Ratio of tasks that should be sporadic (0.0 to 1.0)                         | 0.0                        |
| `--sporadic-deadline-range`     | Range for sporadic task deadline factor relative to MIT (MIN_FACTOR,MAX_FACTOR) | `0.7,1.0`                  |
| `--server-period-range`         | Range for internal component server periods (MIN_PERIOD,MAX_PERIOD)         | `20,100`                   |
| `--server-budget-factor-range`  | Range for internal server budget factor relative to server period (MIN,MAX) | `0.1,0.3`                  |

## Output Files

The generator creates a directory named after the `test-case-name` within the specified `output-dir`. This directory contains three CSV files:

1.  **architecture.csv**: Defines cores.
    * `core_id`: Unique identifier for the core.
    * `speed_factor`: Processing speed relative to a baseline.
    * `scheduler`: Scheduling policy used on the core ('EDF' or 'RM').
2.  **budgets.csv**: Defines components and their interface to cores, including potential server parameters.
    * `component_id`: Unique identifier for the component.
    * `scheduler`: Scheduling policy used *within* the component (inherited from its core).
    * `budget`: Execution budget allocated to the component by the core scheduler.
    * `period`: Period of the component's budget allocation on the core.
    * `core_id`: The core this component is assigned to.
    * `priority`: Priority of the component on the core (used if core scheduler is 'RM').
    * `server_budget`: Budget of the polling server *within* the component (if it contains sporadic tasks). Empty otherwise.
    * `server_period`: Period of the polling server *within* the component (if it contains sporadic tasks). Empty otherwise.
3.  **tasks.csv**: Defines periodic and sporadic tasks.
    * `task_name`: Unique identifier for the task.
    * `wcet`: Worst-Case Execution Time of the task.
    * `period`: Period for periodic tasks, or Minimum Inter-arrival Time (MIT) for sporadic tasks.
    * `component_id`: The component this task is assigned to.
    * `priority`: Priority of the task within the component (used if component scheduler is 'RM', only for periodic tasks).
    * `task_type`: Type of the task ('periodic' or 'sporadic').
    * `deadline`: Relative deadline of the task (equal to period/MIT for periodic, potentially smaller for sporadic).

## Example

The following command generates a potentially schedulable system with 6 cores, 12 components, and 30 tasks (approx. 20% sporadic) with an 85% target total utilization, using specific server parameters:

```bash
python main.py --num-cores=6 --num-components=12 --num-tasks=30 --utilization=85 --test-case-name=adas-sporadic-test --sporadic-ratio=0.2 --server-period-range=50,150 --server-budget-factor-range=0.15,0.25 --seed=42
```

This will create a directory `Test_Cases/generated/adas-sporadic-test/` containing the generated `architecture.csv`, `budgets.csv`, and `tasks.csv` files.

## How It Works

The generator follows these main steps:

1.  **Configuration**: Parse command line arguments using `config.py`.
2.  **Core Generation**: Create cores with specified speed factors and alternating EDF/RM schedulers using `core_generator.py`.
3.  **Utilization Distribution**: Distribute the total system utilization among cores based on their speed factors.
4.  **Component Generation**: Create components, assign them to cores, distribute core utilization among components, and generate component budget/period interfaces and internal server parameters using `component_generator.py`. Assign component priorities if the core uses RM scheduling.
5.  **Task Distribution**: Determine how many tasks (based on total tasks and sporadic ratio) to assign to each component, weighted by component utilization.
6.  **Task Generation**: Create periodic tasks (WCET, period) and sporadic tasks (WCET, MIT, deadline) using `task_generator.py`. Sporadic tasks' deadlines are generated based on their MIT and the `--sporadic-deadline-range` factor. Periodic tasks are assigned RM priorities if the component uses RM scheduling. Sporadic tasks utilize the component's internal server budget/period.
7.  **Schedulability Adjustment (Heuristic)**: If `--unschedulable` is set, heuristically increase WCETs for tasks in a randomly chosen component. If generating a schedulable system, basic checks and adjustments are made (e.g., capping task WCETs based on utilization bounds or server budgets). *Note: Ensuring true schedulability in hierarchical systems with sporadic tasks is complex and may require a separate analysis tool.*
8.  **CSV Generation**: Write the core, component (including server parameters), and task (including type and deadline) definitions to CSV files using `writer.py`.

