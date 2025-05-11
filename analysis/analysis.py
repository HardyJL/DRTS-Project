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
        
        # Get the speed factor for this core
        speed_factor = float(core.speed_factor)
        
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
            # Pass the speed factor to analyze_component
            component_result = self.analyze_component(component, core_bdr, speed_factor)
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



    # This function would be part of your HierarchicalSchedulabilityAnalyzer class
    def analyze_component(self, component: Component, parent_bdr: BDRModel, speed_factor: float) -> Dict:
        """
        Analyze a single component and its tasks.
        Derives minimal BDR for the component, checks internal schedulability,
        and then checks schedulability against the parent BDR using Theorem 1.
        
        Args:
            component: Component to analyze.
            parent_bdr: Parent BDR model (e.g., of the core).
            speed_factor: Speed factor of the core the component runs on.
                
        Returns:
            Dictionary with analysis results for the component.
        """
        
        adjusted_tasks = []
        if component.tasks: # Proceed only if there are tasks
            for task in component.tasks:
                adjusted_task = Task(
                    task_name=task.task_name,
                    wcet=task.wcet / speed_factor, # Apply speed factor
                    period=task.period,
                    component_id=task.component_id,
                    priority=task.priority
                )
                adjusted_tasks.append(adjusted_task)

        # Iteratively find the minimal BDR interface for the component's tasks
        # found_bdr_params will be (alpha, delta) or None
        found_bdr_params = self.find_minimal_bdr_interface(component, adjusted_tasks, parent_bdr.delta)

        derived_alpha = 0.0
        derived_delta = 0.0
        derived_report_budget = 0.0
        derived_report_period = 1.0 # Default period
        component_bdr_for_analysis: BDRModel

        component_initially_schedulable = False # Tracks if tasks are schedulable with found BDR

        if found_bdr_params:
            derived_alpha, derived_delta = found_bdr_params
            component_bdr_for_analysis = BDRModel(derived_alpha, derived_delta)
            # This flag means find_minimal_bdr_interface found parameters 
            # under which it deemed the component's tasks schedulable.
            component_initially_schedulable = True 

            # Convert derived (alpha, delta) back to (Q, P) for reporting
            # This logic aims to provide a representative Q,P pair.
            if abs(derived_alpha - 1.0) < 1e-9:  # Alpha is ~1.0
                derived_report_budget = 1.0
                derived_report_period = 1.0
                # For alpha=1, delta should ideally be 0. If not, it's an unusual BDR.
                if abs(derived_delta) > 1e-9:
                    print(f"    INFO: Component {component.component_id} has derived alpha~1 but delta={derived_delta:.4f}. Reporting Q=1,P=1.")
            elif derived_alpha > 1e-9:  # Alpha is (0, 1)
                if abs(derived_delta) < 1e-9:  # Delta is ~0
                    # BDR (alpha < 1, delta = 0) implies SBF = alpha*t.
                    # Cannot be directly represented by Half-Half P,Q to yield delta=0.
                    # Report Q=alpha, P=1 as a convention.
                    derived_report_budget = derived_alpha
                    derived_report_period = 1.0
                    # Half-Half would give Delta_rep = 2*(1-derived_alpha)
                    print(f"    INFO: Component {component.component_id} derived BDR ({derived_alpha:.4f}, 0.0). Reporting Q={derived_alpha:.4f}, P=1.0. (Note: Half-Half for these Q,P would yield different Delta).")
                else:  # Delta > 0 and Alpha is (0, 1) - Standard case for Half-Half inverse
                    denominator = 2 * (1 - derived_alpha)
                    # This check for denominator should be redundant due to alpha < 1.0 check, but good for safety.
                    if abs(denominator) < 1e-9: 
                        derived_report_budget = derived_alpha
                        derived_report_period = 1.0 # Fallback
                        print(f"    ERROR: Component {component.component_id} alpha very close to 1 with delta > 0, Half-Half period calc issue.")
                    else:
                        derived_report_period = derived_delta / denominator
                        derived_report_budget = derived_alpha * derived_report_period
                        # Ensure period is positive; if calculation results in zero/negative, fallback.
                        if derived_report_period <= 1e-6:
                            print(f"    WARNING: Component {component.component_id} calculated P={derived_report_period:.4f}. Setting P=1.0.")
                            derived_report_period = 1.0
                            derived_report_budget = derived_alpha * derived_report_period
            else:  # Alpha is ~0 (e.g., empty component or tasks with zero WCET)
                derived_report_budget = 0.0
                derived_report_period = 1.0 # Default period for zero budget
                # component_bdr_for_analysis should reflect this (e.g. BDRModel(0, some_delta_or_0))
                # If adjusted_tasks was empty, find_minimal_bdr_interface might return (1.0, 0.0) or similar.
                # Let's ensure component_bdr_for_analysis is consistent if alpha is 0.
                if not adjusted_tasks : # If truly no tasks or zero utilization tasks led to alpha=0
                    component_bdr_for_analysis = BDRModel(0.0, derived_delta) # Or (0.0,0.0) by convention

        else: # No BDR parameters found by find_minimal_bdr_interface
            print(f"    INFO: Component {component.component_id} - find_minimal_bdr_interface failed. Using original budget/period for BDR.")
            # Fallback to using Q,P from budgets.csv if iterative search fails
            # This component will likely be marked unschedulable.
            original_budget = float(component.budget)
            original_period = float(component.period)
            component_bdr_for_analysis = BDRModel.from_periodic_resource(original_budget, original_period)
            
            derived_alpha = component_bdr_for_analysis.alpha # Use alpha from this fallback BDR
            derived_delta = component_bdr_for_analysis.delta # Use delta from this fallback BDR
            # For reporting Q,P, use the ones from the BDR model just created
            derived_report_budget, derived_report_period = component_bdr_for_analysis.to_periodic_resource()
            component_initially_schedulable = False


        # Prepare the component_result dictionary
        component_result = {
            "component_id": component.component_id,
            "scheduler": component.scheduler,
            "alpha": derived_alpha, # The alpha of component_bdr_for_analysis
            "delta": derived_delta, # The delta of component_bdr_for_analysis
            "budget": derived_report_budget,
            "period": derived_report_period,
            "is_schedulable": component_initially_schedulable, # Initial status from find_minimal_bdr_interface or fallback
            "tasks_schedulable": []
        }

        # Verify/Re-verify internal task schedulability with the chosen component_bdr_for_analysis
        # This populates the detailed task status.
        all_tasks_confirmed_schedulable = False
        if adjusted_tasks: # Only if there are tasks
            task_schedulability_details = {}
            if component.scheduler == "EDF":
                task_schedulability_details = component_bdr_for_analysis.get_schedulable_tasks_edf(adjusted_tasks)
            else:  # RM
                task_schedulability_details = component_bdr_for_analysis.get_schedulable_tasks_rm(adjusted_tasks)

            current_all_tasks_sched = True
            for adj_task in adjusted_tasks: # Iterate through adjusted_tasks used for schedulability
                # Find original task for reporting nominal WCET
                original_task = next(t for t in component.tasks if t.task_name == adj_task.task_name)
                is_sched_flag = task_schedulability_details.get(adj_task.task_name, False)
                
                component_result["tasks_schedulable"].append({
                    "task_name": original_task.task_name,
                    "wcet": float(original_task.wcet), # Report nominal WCET
                    "period": float(original_task.period),
                    "is_schedulable": is_sched_flag
                })
                if not is_sched_flag:
                    current_all_tasks_sched = False
            all_tasks_confirmed_schedulable = current_all_tasks_sched
        elif not component.tasks: # No tasks in the component
            all_tasks_confirmed_schedulable = True # Empty component is schedulable internally


        # Update component's schedulability based on this detailed check
        # This overrides the initial_schedulable if the detailed check fails for some reason.
        component_result["is_schedulable"] = all_tasks_confirmed_schedulable
        
        # Now, check Theorem 1 against parent_bdr using the component_bdr_for_analysis
        # Component is only truly schedulable if its tasks are schedulable AND it meets Theorem 1.
        if not component_result["is_schedulable"]:
            # If tasks already made it unschedulable, no need to check Theorem 1 for setting this flag,
            # but we should still report if Theorem 1 would have failed.
            print(f"    INFO: Component {component.component_id} tasks are not schedulable with derived/fallback BDR. Skipping Theorem 1 for its schedulability status.")
        
        # Perform Theorem 1 checks regardless of internal schedulability for complete diagnostics
        theorem1_alpha_ok = True
        if component_bdr_for_analysis.alpha > parent_bdr.alpha:
            theorem1_alpha_ok = False
            component_result["theorem1_alpha_failed"] = True
            print(f"    WARNING: Comp {component.component_id} alpha {component_bdr_for_analysis.alpha:.4f} > Parent alpha {parent_bdr.alpha:.4f} (Theorem 1 Alpha)")

        theorem1_delta_ok = True
        # Strict check: child_delta > parent_delta
        if component_bdr_for_analysis.delta <= parent_bdr.delta:
            theorem1_delta_ok = False
            component_result["theorem1_delta_failed"] = True
            print(f"    WARNING: Comp {component.component_id} delta {component_bdr_for_analysis.delta:.4f} not > Parent delta {parent_bdr.delta:.4f} (Theorem 1 Delta)")

        if not (theorem1_alpha_ok and theorem1_delta_ok):
            component_result["is_schedulable"] = False # Theorem 1 failure makes the component unschedulable in the hierarchy
            print(f"    INFO: Component {component.component_id} failed Theorem 1 check against parent BDR.")
            
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

        print(f"Final result: {results['is_schedulable']}")
    
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
    

    # Inside HierarchicalSchedulabilityAnalyzer class in analysis.py

    # Add delta_step as a class member or constant if you prefer
    # self.delta_search_step = 1.0 # Or some other small positive value

    def find_minimal_bdr_interface(self, component: Component, adjusted_tasks: List[Task], parent_bdr_delta: float) -> Optional[Tuple[float, float]]:
        """
        Iteratively finds a minimal BDR interface (alpha, delta) for the component's tasks,
        considering the parent's delta to ensure hierarchical compatibility.
        """
        if not adjusted_tasks:
            # For an empty component, can be considered schedulable with minimal resource.
            # To satisfy Delta_child > Delta_parent if parent_delta is 0, return a small positive delta.
            # If parent_delta > 0, could return (0.0, parent_delta + self.delta_search_step) or similar.
            # A simple approach:
            # return (0.01, parent_bdr_delta + self.delta_search_step if parent_bdr_delta == 0 else parent_bdr_delta + self.delta_search_step )
            # For now, let's assume (1.0, 0.0) is fine if it then fails Theorem 1, or better:
            if abs(parent_bdr_delta) < 1e-9:
                # Must have child_delta > 0
                return (0.01, 1.0) # Example: minimal alpha, minimal positive delta step
            else:
                # Can technically have child_delta = 0 if parent_delta is very large, but we seek minimal.
                # This case is less critical; the main concern is parent_delta = 0.
                # Let's return parameters that would pass if tasks were minimal.
                return (0.01, parent_bdr_delta + 1.0)


        min_theoretical_alpha = sum(task.wcet / task.period for task in adjusted_tasks)
        if min_theoretical_alpha > 1.0:
            print(f"    DEBUG: Component {component.component_id} task utilization {min_theoretical_alpha:.4f} > 1.0. Fundamentally unschedulable.")
            return None

        # Define Search Parameters (tune these)
        # delta_max heuristic based on hyperperiod of tasks, capped for performance
        periods = [int(task.period) for task in adjusted_tasks if task.period > 0]
        if not periods: # handles cases where no tasks or tasks have zero period
            delta_max = 100.0
        else:
            delta_max = float(lcm_of_list(periods))

        if delta_max > 5000.0: # Cap delta_max
            delta_max = 5000.0
        if delta_max == 0 : delta_max = 100.0 # Ensure delta_max is positive if LCM was 0

        delta_step = 1.0  # Or a smaller configurable value (e.g., self.delta_search_step)
        alpha_step = 0.01

        # Determine starting delta for the search
        start_iter_delta = 0.0
        if abs(parent_bdr_delta) < 1e-9:  # If parent's delta is effectively zero
            start_iter_delta = delta_step    # Child's delta must be > 0

        # If parent_bdr_delta > 0, child could potentially have delta = 0 if that's its true minimum.
        # The Theorem 1 check (child_delta > parent_delta) will handle compatibility.
        # So, `start_iter_delta` can generally be 0.0, and let Theorem 1 filter.
        # The key change was making Theorem 1 strict.
        # However, to directly solve "1-tiny-test-case" where parent_delta=0, child_delta must become > 0.
        # So, `start_iter_delta` must be forced if parent_delta=0.

        print(f"    DEBUG: Searching BDR for {component.component_id}. Min theoretical alpha: {min_theoretical_alpha:.4f}. Max delta: {delta_max}. Starting delta search from: {start_iter_delta:.4f}")

        current_delta = start_iter_delta
        while current_delta <= delta_max:
            min_alpha_for_loop = max(0.01, min_theoretical_alpha)
            if min_theoretical_alpha > 0 and min_theoretical_alpha < 0.01:
                min_alpha_for_loop = min_theoretical_alpha

            current_alpha = min_alpha_for_loop
            while current_alpha <= 1.001: # Loop slightly past 1.0
                alpha_to_test = min(current_alpha, 1.0)
                if alpha_to_test < 0.001 and min_theoretical_alpha == 0 and len(adjusted_tasks) > 0 :
                    alpha_to_test = 0.001 
                elif not adjusted_tasks: # Should be caught earlier, but for safety
                    alpha_to_test = 0.0 # Minimal alpha for empty component
                    # If alpha=0, delta can also be 0 for an empty component that needs no resources
                    # and has no delay in providing nothing.
                    # Or, use a convention like (0.0, a_small_positive_delta) if parent_delta=0.
                    # This case is tricky; let's assume (0.0, 0.0) if truly empty, handled by earlier check.


                test_bdr = BDRModel(alpha_to_test, current_delta)
                is_component_schedulable = False
                if component.scheduler == "EDF":
                    is_component_schedulable = test_bdr.is_schedulable_edf_workload(adjusted_tasks)
                else:  # RM
                    is_component_schedulable = test_bdr.is_schedulable_rm_workload(adjusted_tasks)

                if is_component_schedulable:
                    print(f"    DEBUG: Found schedulable BDR for {component.component_id}: (alpha={alpha_to_test:.4f}, delta={current_delta:.4f})")
                    return (alpha_to_test, current_delta)

                current_alpha += alpha_step

            # If current_delta was 0 and we didn't find a solution (e.g. only alpha=1 was needed but tasks util < 1),
            # and start_iter_delta was also 0 (because parent_delta > 0), we must ensure next delta is > 0.
            if abs(current_delta) < 1e-9 and abs(start_iter_delta) < 1e-9: # If we just checked delta=0
                current_delta = delta_step # Ensure next check is for positive delta
            else:
                current_delta += delta_step


        print(f"    DEBUG: No suitable BDR found for component {component.component_id} within search range.")
        return None


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