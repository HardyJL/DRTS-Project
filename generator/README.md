# Hierarchical Taskset Generator

A tool for generating synthetic tasksets for hierarchical scheduling systems with multiple cores, components, and tasks using EDF (Earliest Deadline First) and RM (Rate Monotonic) scheduling algorithms.

## Overview

This generator creates realistic test cases for evaluating hierarchical scheduling algorithms, particularly for Advanced Driver-Assistance Systems (ADAS) running on multicore platforms. The generator produces:

- Cores with varying speed factors and schedulers
- Components assigned to cores with budgets and periods
- Tasks with execution times and periods assigned to components

## Project Structure

The project follows an object-oriented design with the following structure:

```
generator/
├── __init__.py         # Package exports
├── config.py           # Configuration parameter handling
├── core_generator.py   # Core generation logic
├── component_generator.py # Component generation logic
├── task_generator.py   # Task generation logic
├── utils.py            # Utility functions
└── writer.py           # CSV file output handling

main.py                 # Entry point
```

## Installation

Clone the repository and make sure you have the required dependencies:

```bash
# Clone the repository
git clone https://github.com/yourusername/hierarchical-taskset-generator.git
cd hierarchical-taskset-generator

# Install dependencies
pip install numpy
```

## Usage

Run the generator with default parameters:

```bash
python main.py
```

Or customize the generation with command line arguments:

```bash
python main.py --num-cores=8 --num-components=16 --num-tasks=40 --utilization=80
```

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--num-cores` | Number of cores in the system | 4 |
| `--num-components` | Number of components across all cores | 8 |
| `--num-tasks` | Number of tasks across all components | 20 |
| `--utilization` | Total system utilization in percent | 70.0 |
| `--output-dir` | Directory to output the generated files | Test_Cases/generated |
| `--test-case-name` | Name of the test case | hierarchical-test-case |
| `--speed-factor-range` | Range for core speed factors (MIN,MAX) | 0.5,1.5 |
| `--unschedulable` | Generate an unschedulable system | False |
| `--seed` | Random seed for reproducibility | None |

## Output Files

The generator creates a directory within the specified output directory containing three CSV files:

1. **architecture.csv** - Core definitions with speed factors and schedulers
2. **budgets.csv** - Component definitions with budgets, periods, and assignments to cores
3. **tasks.csv** - Task definitions with execution times, periods, and assignments to components

## Example

The following command generates a schedulable system with 6 cores, 12 components, and 30 tasks with an 85% total utilization:

```bash
python main.py --num-cores=6 --num-components=12 --num-tasks=30 --utilization=85 --test-case-name=adas-test-case
```

This will create a directory `Test_Cases/generated/adas-test-case/` containing the generated CSV files.

## How It Works

The generator follows these steps:

1. **Configuration**: Parse command line arguments and set up generation parameters
2. **Core Generation**: Create cores with varying speed factors
3. **Utilization Distribution**: Distribute the total system utilization among cores
4. **Component Generation**: Create components and assign them to cores
5. **Task Distribution**: Determine how many tasks to assign to each component
6. **Task Generation**: Create tasks with execution times and periods
7. **Schedulability Adjustment**: Adjust task parameters to ensure the system is schedulable or unschedulable as requested
8. **CSV Generation**: Write the results to CSV files

## License

MIT License