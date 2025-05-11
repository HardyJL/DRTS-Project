import os
import sys
import csv
import math
from typing import List, Dict, Tuple, Optional, Union, Any
from functools import reduce
from bdr_model import BDRModel
from core import Core, Component, Task, Solution
from csv_functions import load_models_from_csv, write_solutions_to_csv, lcm_of_list, load_csv_data

class HierarchicalSchedulabilityAnalyzer:
    """
    Main class for analyzing hierarchical schedulability using the BDR model.
    """
    
    def __init__(self, folder_path: str):
        """
        Initialize the analyzer with paths to input files.
        
        Args:
            folder_path: Path to the folder containing input files
        """
        self.folder_path = folder_path
        self.architecture_path = os.path.join(folder_path, "architecture.csv")
        self.tasks_path = os.path.join(folder_path, "tasks.csv")
        self.budgets_path = os.path.join(folder_path, "budgets.csv")
        
        # Verify files exist
        for path in [self.architecture_path, self.tasks_path, self.budgets_path]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Required file not found: {path}")
        
        # Load data
        self.cores = load_csv_data(self.architecture_path, Core)
        self.tasks = load_csv_data(self.tasks_path, Task)
        self.components = load_csv_data(self.budgets_path, Component)
        
        # Build relationships
        self._build_relationships()
        
        # Results
        self.analysis_results = {}
    
    def _build_relationships(self):
        """Build relationships between cores, components, and tasks."""
        # Associate tasks with components
        for component in self.components:
            component.tasks = [task for task in self.tasks if task.component_id == component.component_id]
        
        # Associate components with cores
        for core in self.cores:
            core.components = [comp for comp in self.components if comp.core_id == core.core_id]
    
    def analyze_system(self) -> Dict:
        """
        Analyze the entire system, including all cores and components.
        
        Returns:
            Dictionary with analysis results
        """
        system_results = {
            "is_schedulable": True,
            "cores": []
        }
        
        # Analyze each core
        for core in self.cores:
            core_result = self.analyze_core(core)
            system_results["cores"].append(core_result)
            
            # System is schedulable only if all cores are schedulable
            if not core_result["is_schedulable"]:
                system_results["is_schedulable"] = False
        
        return system_results
    
    def analyze_core(self, core: Core) -> Dict:
        """
        Analyze a single core and its components.
        
        Args:
            core: Core to analyze
            
        Returns:
            Dictionary with analysis results for the core
        """
        # Create BDR model for the core (top level - full availability)
        core_bdr = BDRModel(1.0, 0.0)
        
        core_result = {
            "core_id": core.core_id,
            "alpha": core_bdr.alpha,
            "delta": core_bdr.delta,
            "is_schedulable": True,
            "components": []
        }
        
        # Analyze each component on this core
        component_bdrs = []
        for component in core.components:
            component_result = self.analyze_component(component, core_bdr)
            core_result["components"].append(component_result)
            
            # Get component's BDR model for Theorem 1 check
            component_bdr = BDRModel(component_result["alpha"], component_result["delta"])
            component_bdrs.append(component_bdr)
            
            # Core is schedulable only if all components are schedulable
            if not component_result["is_schedulable"]:
                core_result["is_schedulable"] = False
        
        # Check overall schedulability using Theorem 1
        if component_bdrs:
            theorem1_satisfied = BDRModel.check_theorem1_schedulability(core_bdr, component_bdrs)
            if not theorem1_satisfied:
                core_result["is_schedulable"] = False
                core_result["theorem1_failed"] = True
        
        return core_result
    
    def analyze_component(self, component: Component, parent_bdr: BDRModel) -> Dict:
        """
        Analyze a single component and its tasks.
        
        Args:
            component: Component to analyze
            parent_bdr: Parent BDR model
            
        Returns:
            Dictionary with analysis results for the component
        """
        # Create BDR model for the component
        component_bdr = BDRModel.from_periodic_resource(float(component.budget), float(component.period))
        
        # Get budget and period from the half-half algorithm
        budget, period = component_bdr.to_periodic_resource()
        
        component_result = {
            "component_id": component.component_id,
            "scheduler": component.scheduler,
            "alpha": component_bdr.alpha,
            "delta": component_bdr.delta,
            "budget": budget,
            "period": period,
            "is_schedulable": True,
            "tasks_schedulable": []
        }
        
        # Check if tasks are schedulable under this component
        if component.scheduler == "EDF":
            task_schedulability = component_bdr.get_schedulable_tasks_edf(component.tasks)
        else:  # RM or others
            task_schedulability = component_bdr.get_schedulable_tasks_rm(component.tasks)
        
        # Add task results
        for task in component.tasks:
            is_task_schedulable = task_schedulability.get(task.task_name, False)
            
            task_result = {
                "task_name": task.task_name,
                "wcet": float(task.wcet),
                "period": float(task.period),
                "is_schedulable": is_task_schedulable
            }
            
            component_result["tasks_schedulable"].append(task_result)
            
            # Component is schedulable only if all tasks are schedulable
            if not is_task_schedulable:
                component_result["is_schedulable"] = False
        
        # Check Theorem 1 against parent
        theorem1_satisfied = True
        if component_bdr.alpha > parent_bdr.alpha:
            theorem1_satisfied = False
            component_result["theorem1_alpha_failed"] = True

        # Special case for delta check
        if component_bdr.delta <= parent_bdr.delta and not (component_bdr.delta == 0 and parent_bdr.delta == 0):
            theorem1_satisfied = False
            component_result["theorem1_delta_failed"] = True
        
        
        if not theorem1_satisfied:
            component_result["is_schedulable"] = False
        
        return component_result
    
    def export_results_to_csv(self, results: Dict, output_path: str = None) -> None:
        """
        Export analysis results to a CSV file.
        
        Args:
            results: Analysis results dictionary
            output_path: Path to output CSV file (default: solutions.csv in the same folder)
        """
        if output_path is None:
            output_path = os.path.join(self.folder_path, "solutions.csv")
        
        rows = []
        
        # Extract task-level results
        for core_result in results["cores"]:
            for component_result in core_result["components"]:
                component_id = component_result["component_id"]
                component_schedulable = 1 if component_result["is_schedulable"] else 0
                
                for task_result in component_result["tasks_schedulable"]:
                    rows.append({
                        "task_name": task_result["task_name"],
                        "component_id": component_id,
                        "task_schedulable": 1 if task_result["is_schedulable"] else 0,
                        "avg_response_time": 0.0,  # Not calculated in analysis
                        "max_response_time": 0.0,  # Not calculated in analysis
                        "component_schedulable": component_schedulable
                    })
        
        # Write to CSV
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = ["task_name", "component_id", "task_schedulable", 
                         "avg_response_time", "max_response_time", "component_schedulable"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        
        print(f"Results exported to {output_path}")
    
    def print_analysis_results(self, results: Dict) -> None:
        """
        Print analysis results in a human-readable format.
        
        Args:
            results: Analysis results dictionary
        """
        print("\n===== Hierarchical Schedulability Analysis Results =====\n")
        print(f"System Schedulable: {'YES' if results['is_schedulable'] else 'NO'}")
        
        for core_result in results["cores"]:
            print(f"\nCore: {core_result['core_id']}")
            print(f"  Availability Factor (α): {core_result['alpha']:.4f}")
            print(f"  Partition Delay (Δ): {core_result['delta']:.4f}")
            print(f"  Schedulable: {'YES' if core_result['is_schedulable'] else 'NO'}")
            
            if core_result.get("theorem1_failed"):
                print("  NOTE: Failed Theorem 1 check for components")
            
            for component_result in core_result["components"]:
                print(f"\n  Component: {component_result['component_id']}")
                print(f"    Scheduler: {component_result['scheduler']}")
                print(f"    Availability Factor (α): {component_result['alpha']:.4f}")
                print(f"    Partition Delay (Δ): {component_result['delta']:.4f}")
                print(f"    Budget: {component_result['budget']:.4f}")
                print(f"    Period: {component_result['period']:.4f}")
                print(f"    Schedulable: {'YES' if component_result['is_schedulable'] else 'NO'}")
                
                if component_result.get("theorem1_alpha_failed"):
                    print(f"    WARNING: Component α ({component_result['alpha']:.4f}) exceeds core α ({core_result['alpha']:.4f})")
                
                if component_result.get("theorem1_delta_failed"):
                    print(f"    WARNING: Component Δ ({component_result['delta']:.4f}) <= core Δ ({core_result['delta']:.4f})")
                
                print("\n    Tasks:")
                for task_result in component_result["tasks_schedulable"]:
                    print(f"      Task: {task_result['task_name']}")
                    print(f"        WCET: {task_result['wcet']:.4f}")
                    print(f"        Period: {task_result['period']:.4f}")
                    print(f"        Schedulable: {'YES' if task_result['is_schedulable'] else 'NO'}")
        
        print("\n" + "="*50)
    
    def run_analysis(self) -> Dict:
        """
        Run the complete analysis and return results.
        
        Returns:
            Analysis results dictionary
        """
        # Run analysis
        results = self.analyze_system()
        
        # Print results
        self.print_analysis_results(results)
        
        # Export results
        self.export_results_to_csv(results)
        
        return results


def main():
    """Main function to run the analysis tool."""
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python analysis.py <test_case_folder>")
        return 1
    
    test_case_folder = sys.argv[1]
    
    try:
        # Create analyzer
        analyzer = HierarchicalSchedulabilityAnalyzer(test_case_folder)
        
        # Run analysis
        analyzer.run_analysis()
        
        return 0
    except Exception as e:
        print(f"Error running analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())