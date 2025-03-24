# 02225 DRTS Project: ADAS Multicore Scheduling Simulation and Analysis

## Description

This project involves developing a simulator and an analysis tool for an Advanced Driver-Assistance System (ADAS) running on a multicore platform with hierarchical scheduling.  The goal is to simulate system behavior and analyze schedulability to ensure tasks meet deadlines.

## Getting Started

### Prerequisites

*   Python 3.x
*   `pip` package installer

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [repository-url]
    cd [project-directory]
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    ```

3.  **Activate the virtual environment:**
    *   **On Linux/macOS:**
        ```bash
        source venv/bin/activate
        ```
    *   **On Windows:**
        ```bash
        venv\Scripts\activate
        ```

4.  **Install dependencies (if any, list them in `requirements.txt` later):**
    ```bash
    pip install -r requirements.txt # If you create a requirements.txt file
    ```

### Running the Project

*   **Simulator:**  Run the simulator script using Python.
    ```bash
    python simulator/simulator.py [path/to/input_file.txt]
    ```
*   **Analysis Tool:** Run the analysis tool script using Python.
    ```bash
    python analysis_tool/analysis_tool.py [path/to/input_file.txt]
    ```
    *Replace `simulator/simulator.py`, `analysis_tool/analysis_tool.py`, and `[path/to/input_file.txt]` with the actual paths to your scripts and input files.*

## Usage

The project consists## Project Scope and Ideas: 02225 DRTS - ADAS Multicore Scheduling

**Project Goal:**  To model, simulate, and analyze the real-time scheduling of an Advanced Driver-Assistance System (ADAS) on a multicore platform.  We aim to ensure the ADAS application, composed of critical and non-critical tasks, meets its timing requirements.

**Key Project Ideas:**

*   **Hierarchical Scheduling:** Implement and analyze a hierarchical scheduling approach on each core of a multicore system. This involves multiple levels of schedulers managing different types of tasks.

*   **Bounded Delay Resource (BDR) Model:** Utilize the BDR model to abstract and manage resource allocation between different levels of the hierarchical scheduling system. This model helps in compositional analysis.

*   **Task Types:**  Model the ADAS application using:
    *   **Hard Periodic Tasks:** Representing critical functions with strict deadlines and fixed periods.
    *   **Soft Sporadic Tasks:** Representing non-critical functions with minimum inter-arrival times and deadlines.

*   **Scheduling Algorithms:** Implement and analyze common real-time scheduling algorithms within the hierarchical framework:
    *   **Earliest Deadline First (EDF):**  A dynamic priority scheduler.
    *   **Fixed Priority Scheduling (FPS) with Rate Monotonic (RM):** A static priority scheduler and priority assignment policy.

*   **Simulator Development:** Build a simulator to mimic the execution of the ADAS tasks under the defined hierarchical scheduling system.  The simulator will use BDR resource supply and report task response times and resource utilization.

*   **Analysis Tool Development:** Create an analysis tool to perform schedulability analysis. This tool will:
    *   Calculate BDR interface parameters for components based on their task workloads and scheduling algorithms.
    *   Implement schedulability tests using Demand Bound Functions (DBF) and Supply Bound Functions (SBF).
    *   Compare the results of the analysis with the simulator outputs.

*   **Compositional Analysis:** Apply compositional analysis techniques to analyze the hierarchical system's schedulability by considering resource demand and supply at each level.

**Potential Scope Extensions:**

*   Worst-Case Response Time (WCRT) calculation.
*   Exploration of alternative resource models (PRM, EDP).
*   Modeling and analysis of inter-task communication.
*   Optimization of core assignments and resource model parameters.

**Overall, the project focuses on applying real-time scheduling theory and simulation to a practical ADAS example using a hierarchical and compositional approach for multicore systems.** of two main components:

*   **Simulator:** Simulates the execution of ADAS tasks on a multicore platform using hierarchical scheduling and BDR resource model. It reads input files describing the application, platform, and scheduling configurations. The simulator outputs task response times and resource utilization metrics.

*   **Analysis Tool:**  Analyzes the schedulability of the ADAS task set. It calculates BDR interface parameters for components and performs schedulability analysis based on demand and supply bound functions. The tool reports schedulability results.

Both tools use the same input file format to describe the system.  Refer to the project documentation or example input files for the input file structure.

## Project Structure (Example - Adapt as needed)
