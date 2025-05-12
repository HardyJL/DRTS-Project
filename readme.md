# Readme for DRTS Project - Group 36

## Description

This project simulates and analyzes the scheduling of an Advanced Driver-Assistance System (ADAS) on a multicore platform. It includes a simulator and an analysis tool to ensure tasks meet deadlines using hierarchical scheduling.

## Getting Started

### Prerequisites

- Python 3.x
- `pip` package installer

### Installation

1. **Clone the repository:**
   ```bash
   git clone [repository-url]
   cd [project-directory]
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment:**
   - **On Linux/macOS:**
     ```bash
     source venv/bin/activate
     ```
   - **On Windows:**
     ```bash
     venv\Scripts\activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Project

#### Simulator
Run the simulator using the following command:
```bash
python main.py [path/to/test-case-folder] [simulation_time_factor]
```
- Example:
  ```bash
  python main.py Test-Cases/2-small-test-case 20
  ```

#### Debugging
To debug the project, use the provided VS Code launch configuration:
```json
{
  "name": "Python Debugger: Current File with Arguments",
  "type": "debugpy",
  "request": "launch",
  "program": "main.py",
  "console": "integratedTerminal",
  "args": "Test-Cases/2-small-test-case 20"
}
```

## Project Structure

- **`main.py`**: Entry point for the simulator.
- **`models/`**: Contains core classes like `Task`, `Core`, `Component`, and `Solution`.
- **`scheduler/`**: Implements scheduling algorithms (EDF, RM).
- **`simulation/`**: Contains the `Simulation` class to simulate task execution.
- **`generator/`**: Contains an implementation for a hierarchical test case generator.
- **`csv_functions/`**: Handles loading models from CSV files.
- **`Test-Cases/`**: Includes test cases in CSV format.

## Input File Format

### `tasks.csv`
Defines tasks with the following columns:
- `task_name`: Name of the task.
- `wcet`: Worst-case execution time.
- `period`: Task period.
- `component_id`: Component ID.
- `priority`: Task priority (for RM scheduling).

### `architecture.csv`
Defines the hardware platform:
- `core_id`: Core identifier.
- `speed_factor`: Core speed relative to nominal speed.
- `scheduler`: Core-level scheduler (EDF or RM).

### `budgets.csv`
Defines component budgets and periods:
- `component_id`: Component identifier.
- `scheduler`: Component-level scheduler (EDF or RM).
- `budget`: Resource allocation for the component.
- `period`: Component period.
- `core_id`: Core assignment.

## Output

The simulator outputs task response times and schedulability results in the following format:
```csv
task_name,component_id,task_schedulable,avg_response_time,max_response_time,component_schedulable
Task_1,Component_1,1,10.0,15.0,1
Task_2,Component_1,0,20.0,25.0,0
```

## Key Features

- **Hierarchical Scheduling**: Supports EDF and RM scheduling at both core and component levels.
- **Simulation**: Simulates task execution and calculates response times.
- **Analysis**: Performs schedulability analysis using demand and supply bound functions.
- **Generation**: Generates a range of example test cases according to given parameters

## Example Test Case

To run the simulator with a test case:
1. Navigate to the `Test-Cases/` folder.
2. Select a test case folder (e.g., `2-small-test-case`).
3. Run the simulator:
   ```bash
   python main.py Test-Cases/2-small-test-case 20
   ```


To run the analysis tool with a test case:
1. Navigate to the `Test-Cases/` folder.
2. Select a test case folder (e.g., `2-small-test-case`).
3. Run the analysis tool:
   ```bash
   python analysis.py Test-Cases/2-small-test-case
   ```
