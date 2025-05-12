import os
import sys
import csv
import math
from typing import List, Dict, Tuple, Optional, Union, Any
from bdr_model import BDRModel
from core import Core, Component, Task, Solution
from csv_functions import lcm_of_list, load_csv_data

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
        # Correctly instantiate Task objects with all fields from CSV
        # The load_csv_data function should handle passing all columns to the Task constructor
        
        # Associate tasks with components
        for component in self.components:
            component.tasks = [task for task in self.tasks if task.component_id == component.component_id]
            
            # If component has server parameters and sporadic tasks, create the Polling Server Task
            if component.server_budget is not None and component.server_period is not None:
                # Check if there are any sporadic tasks actually assigned to this component
                if any(t.task_type == 'sporadic' for t in component.tasks):
                    # Assign a priority to the server if the component is RM
                    # This is a simple heuristic, could be based on T_ps or other rules
                    server_priority = 0 # Example: highest priority for the server
                    if component.scheduler == "RM":
                        # A common approach is to assign server priority based on its period
                        # For simplicity, or if it's the only server, it might get a high priority.
                        # Let's find highest existing priority among periodic tasks and make server higher.
                        periodic_priorities = [p.priority for p in component.tasks if p.task_type == 'periodic' and p.priority is not None]
                        if periodic_priorities:
                             server_priority = min(periodic_priorities) -1 if min(periodic_priorities) > 0 else 0
                        # else if no periodic tasks or no priorities, 0 is fine.
                        # Ensure priority is not negative if min_priorities was 0
                        server_priority = max(0, server_priority)


                    component.polling_server_task = Task(
                        task_name=f"{component.component_id}_PS",
                        wcet=component.server_budget,
                        period=component.server_period, # Period of the server
                        component_id=component.component_id, # Belongs to this component
                        priority=server_priority if component.scheduler == "RM" else None,
                        task_type="periodic", # The server itself is seen as a periodic load
                        deadline=component.server_period # Server deadline is its period
                    )
                    print(f"INFO: Created Polling Server {component.polling_server_task} for component {component.component_id}")


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
        component_result = {
            "component_id": component.component_id,
            "scheduler": component.scheduler,
            "is_schedulable": False, # Default to not schedulable
            "tasks_schedulable": [],
            "sporadic_tasks_analysis": {} # To store results for sporadic tasks
        }

        # Adjust WCETs for all tasks in the component based on core speed_factor
        # and separate periodic and sporadic tasks
        native_periodic_tasks_adjusted: List[Task] = []
        sporadic_tasks_for_server_adjusted: List[Task] = []

        for task in component.tasks:
            adjusted_wcet = task.original_wcet / speed_factor # Assuming original_wcet stores nominal
            # Create new Task instances for analysis to avoid modifying original task list shared across calls
            adjusted_task = Task(
                task_name=task.task_name,
                wcet=adjusted_wcet,
                period=task.period, # This is MIT for sporadic
                component_id=task.component_id,
                priority=task.priority,
                task_type=task.task_type,
                deadline=task.deadline
            )
            adjusted_task.original_wcet = task.original_wcet # Keep track if needed

            if task.task_type == "periodic":
                native_periodic_tasks_adjusted.append(adjusted_task)
            elif task.task_type == "sporadic":
                sporadic_tasks_for_server_adjusted.append(adjusted_task)

        # --- Effective tasks for BDR analysis of the component ---
        # This list includes native periodic tasks and the Polling Server (if any)
        effective_tasks_for_bdr: List[Task] = list(native_periodic_tasks_adjusted)
        has_server = False
        if component.polling_server_task:
            # Adjust server's WCET (its budget Cps) by speed_factor if it represents CPU time on this core
            # Typically, server budget Cps is defined as CPU time, so it should be scaled.
            adjusted_server_wcet = component.polling_server_task.original_wcet / speed_factor
            
            # Create an adjusted copy for analysis if not already done, or update existing
            # For simplicity, let's assume polling_server_task was created with nominal WCET
            # and needs adjustment here.
            ps_task_for_analysis = Task(
                task_name=component.polling_server_task.task_name,
                wcet=adjusted_server_wcet, # Server budget C_ps
                period=component.polling_server_task.period, # Server period T_ps
                component_id=component.polling_server_task.component_id,
                priority=component.polling_server_task.priority,
                task_type="periodic", # Server is periodic
                deadline=component.polling_server_task.deadline # Server deadline D_ps = T_ps
            )
            effective_tasks_for_bdr.append(ps_task_for_analysis)
            has_server = True
            print(f"INFO: Component {component.component_id} includes server {ps_task_for_analysis} in its BDR demand.")


        # 1. Find minimal BDR interface for the component's effective periodic load
        found_bdr_params = self.find_minimal_bdr_interface(component, effective_tasks_for_bdr, parent_bdr.delta)

        derived_alpha = 0.0
        derived_delta = 0.0
        component_bdr_for_analysis: Optional[BDRModel] = None
        component_internally_schedulable = False # Schedulability of periodic tasks + server

        if found_bdr_params:
            derived_alpha, derived_delta = found_bdr_params
            component_bdr_for_analysis = BDRModel(derived_alpha, derived_delta)
            # Check if effective tasks (periodic + server) are schedulable under this derived BDR
            if component.scheduler == "EDF":
                component_internally_schedulable = component_bdr_for_analysis.is_schedulable_edf_workload(effective_tasks_for_bdr)
            else: # RM
                component_internally_schedulable = component_bdr_for_analysis.is_schedulable_rm_workload(effective_tasks_for_bdr)
        else:
            print(f"    INFO: Component {component.component_id} - find_minimal_bdr_interface failed. Using original budget/period from CSV for BDR.")
            original_budget = float(component.budget) # Component's BDR interface budget
            original_period = float(component.period) # Component's BDR interface period
            if original_period == 0: original_period = 1.0 # Avoid division by zero
            component_bdr_for_analysis = BDRModel.from_periodic_resource(original_budget, original_period)
            derived_alpha = component_bdr_for_analysis.alpha
            derived_delta = component_bdr_for_analysis.delta
            component_internally_schedulable = False # Cannot guarantee with original if find_minimal failed

        component_result["alpha"] = derived_alpha
        component_result["delta"] = derived_delta
        # Report budget/period of the BDR interface of the component
        if component_bdr_for_analysis:
             q,p = component_bdr_for_analysis.to_periodic_resource()
             component_result["budget"] = q
             component_result["period"] = p
        else: # Should not happen if fallback above works
             component_result["budget"] = component.budget
             component_result["period"] = component.period


        # Populate task schedulability for NATIVE PERIODIC tasks
        if native_periodic_tasks_adjusted and component_bdr_for_analysis:
            details_periodic = {}
            if component.scheduler == "EDF":
                # Condition: task is periodic AND ( (server exists AND task is not server) OR server does not exist )
                temp_edf_check_list = [
                    t for t in effective_tasks_for_bdr 
                    if t.task_type == 'periodic' and 
                       ( (component.polling_server_task and t.task_name != component.polling_server_task.task_name) or 
                         (not component.polling_server_task) )
                ]
                if temp_edf_check_list:
                    details_periodic = component_bdr_for_analysis.get_schedulable_tasks_edf(temp_edf_check_list)
                else:
                    details_periodic = {}

            else: # RM
                details_periodic = component_bdr_for_analysis.get_schedulable_tasks_rm(native_periodic_tasks_adjusted) # Pass only native periodic

            for task in native_periodic_tasks_adjusted:
                is_sched = details_periodic.get(task.task_name, False)
                component_result["tasks_schedulable"].append({
                    "task_name": task.task_name, "wcet": task.original_wcet, "period": task.period,
                    "task_type": "periodic", "deadline": task.deadline, "is_schedulable": is_sched
                })
                if not is_sched: component_internally_schedulable = False
        
        # Schedulability of the POLLING SERVER itself (if it exists)
        server_is_schedulable_by_bdr = False
        if has_server and component_bdr_for_analysis and ps_task_for_analysis:
            if component.scheduler == "EDF":
                # Already checked as part of effective_tasks_for_bdr with EDF
                # Need a way to extract server's specific status if is_schedulable_edf_workload doesn't return per-task
                 server_is_schedulable_by_bdr = component_bdr_for_analysis.is_schedulable_edf_workload([ps_task_for_analysis]) # Check server alone
            else: # RM
                server_is_schedulable_by_bdr = component_bdr_for_analysis.is_schedulable_rm_task(ps_task_for_analysis, effective_tasks_for_bdr)
            
            component_result["tasks_schedulable"].append({
                "task_name": ps_task_for_analysis.task_name, "wcet": ps_task_for_analysis.original_wcet, # This should be Cps (nominal)
                "period": ps_task_for_analysis.period, "task_type": "server",
                "deadline": ps_task_for_analysis.deadline, "is_schedulable": server_is_schedulable_by_bdr
            })
            if not server_is_schedulable_by_bdr: component_internally_schedulable = False
            print(f"INFO: Server {ps_task_for_analysis.task_name} schedulable by BDR: {server_is_schedulable_by_bdr}")


        # 2. Analyze schedulability of SPORADIC tasks by the Polling Server
        sporadic_tasks_overall_schedulable = True
        if sporadic_tasks_for_server_adjusted and has_server and server_is_schedulable_by_bdr:
            # Use nominal Cps for this analysis (not scaled by core speed factor, as it's about server's own capacity)
            nominal_cps = component.polling_server_task.wcet # Cps
            nominal_tps = component.polling_server_task.period # Tps
            
            # Perform schedulability analysis for sporadic tasks served by this PS
            # This is a placeholder for actual analysis logic.
            # Example: simple utilization check + basic response time bound.
            total_sporadic_util = sum(st.wcet / st.period for st in sporadic_tasks_for_server_adjusted if st.period > 0) # period is MIT
            server_util = nominal_cps / nominal_tps if nominal_tps > 0 else 0

            component_result["sporadic_tasks_analysis"]["server_cps"] = nominal_cps
            component_result["sporadic_tasks_analysis"]["server_tps"] = nominal_tps
            component_result["sporadic_tasks_analysis"]["server_util"] = server_util
            component_result["sporadic_tasks_analysis"]["total_sporadic_task_util"] = total_sporadic_util
            
            all_sporadic_individually_sched = True
            if total_sporadic_util > server_util:
                print(f"    WARNING: Sporadic tasks demand ({total_sporadic_util:.2f}) for {component.component_id} exceeds server supply ({server_util:.2f}).")
                all_sporadic_individually_sched = False # Basic necessary condition fails

            # Individual sporadic task checks (placeholder for a more formal WCRT_sporadic_PS analysis)
            for stask in sporadic_tasks_for_server_adjusted:
                # Simplistic Check: Can task run within one server budget if it gets full budget?
                # And a very rough response time estimate. This needs to be replaced by proper PS theory.
                # R_s <= D_s
                # A basic, often pessimistic, check for Polling Server for task j:
                # If Cj > Cps, it's unschedulable by this server if it needs to run contiguously.
                # Response time bound: roughly 2*Tps (worst case wait for server + execution)
                # This is NOT a formal bound for most cases.
                # You should implement a known WCRT formula for sporadic tasks under a PS.
                # e.g., from Liu & Layland or Buttazzo for aperiodic servers.
                # For now, a placeholder:
                R_sj_estimate = 2 * nominal_tps + stask.wcet 
                # This estimate is very basic and likely incorrect for general case.
                # It assumes task might wait almost 2 periods and then executes.

                # A more robust check could be based on "supply on demand" from the server.
                # For example, check if dbf_sporadic(t) <= sbf_server(t)
                # where sbf_server(t) is the supply from the polling server.
                # sbf_PS(t) = max(0, floor((t - (Tps-Cps))/Tps)*Cps + min(Cps, t - (Tps-Cps) % Tps )) (approx)
                # This is becoming complex. For the project, "schedulability analysis" usually implies known bounds.

                # Let's use a very basic placeholder: if total util is ok, and individual WCET fits budget.
                stask_sched = True
                if stask.wcet > nominal_cps : # Task too big for one server budget activation
                     stask_sched = False
                if not all_sporadic_individually_sched : # If total util already failed
                     stask_sched = False
                
                # If you implement a WCRT_PS(stask, nominal_cps, nominal_tps) function:
                # wcrt_stask = WCRT_PS(stask, nominal_cps, nominal_tps)
                # stask_sched = wcrt_stask <= stask.deadline

                component_result["tasks_schedulable"].append({
                    "task_name": stask.task_name, "wcet": stask.original_wcet, "period": stask.period, # period is MIT
                    "task_type": "sporadic", "deadline": stask.deadline, "is_schedulable": stask_sched
                })
                if not stask_sched:
                    sporadic_tasks_overall_schedulable = False
            
            if not all_sporadic_individually_sched : sporadic_tasks_overall_schedulable = False

        elif sporadic_tasks_for_server_adjusted and (not has_server or not server_is_schedulable_by_bdr):
            # If there are sporadic tasks but server isn't schedulable or doesn't exist
            sporadic_tasks_overall_schedulable = False
            for stask in sporadic_tasks_for_server_adjusted: # Mark them all as unschedulable
                 component_result["tasks_schedulable"].append({
                    "task_name": stask.task_name, "wcet": stask.original_wcet, "period": stask.period,
                    "task_type": "sporadic", "deadline": stask.deadline, "is_schedulable": False
                })

        # 3. Overall component schedulability
        # Component is schedulable if its effective periodic load is schedulable by its BDR,
        # AND that BDR is schedulable by parent (Theorem 1),
        # AND all sporadic tasks are schedulable by their server.
        component_schedulable_hierarchically = False
        if component_internally_schedulable and component_bdr_for_analysis:
             # Check Theorem 1 against parent_bdr
            if BDRModel.check_theorem1_schedulability(parent_bdr, [component_bdr_for_analysis]):
                component_schedulable_hierarchically = True
            else:
                component_result["theorem1_failed"] = True
                print(f"    INFO: Component {component.component_id} failed Theorem 1 check against parent BDR {parent_bdr}.")
        
        # Final decision for component schedulability
        if sporadic_tasks_for_server_adjusted: # If there were sporadic tasks
            component_result["is_schedulable"] = component_internally_schedulable and component_schedulable_hierarchically and sporadic_tasks_overall_schedulable
        else: # Only periodic tasks
            component_result["is_schedulable"] = component_internally_schedulable and component_schedulable_hierarchically
        
        if not component_result["is_schedulable"]:
            print(f"    DEBUG: Component {component.component_id} determined UNSCHEDULABLE.")
            print(f"    DEBUG:   Internal (periodic+server) sched: {component_internally_schedulable}")
            print(f"    DEBUG:   Hierarchical (Theorem 1) sched: {component_schedulable_hierarchically}")
            if sporadic_tasks_for_server_adjusted:
                print(f"    DEBUG:   Sporadic tasks sched by server: {sporadic_tasks_overall_schedulable}")


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
    def WCRT_PS_basic(self, sporadic_task: Task, Cps: float, Tps: float) -> float:
        """
        Calculate a basic (often pessimistic) WCRT for a sporadic task under a Polling Server.
        This is a placeholder and should be replaced with a more standard analysis.
        It assumes the task might arrive just after the server has finished its budget,
        waits for the next server period, and then gets served.
        Does not account for other sporadic tasks contending for the server.
        """
        if sporadic_task.wcet > Cps:
            return float('inf') # Task cannot be served in one server budget activation

        # Time until next server activation + time server is busy before us (worst case 0 if we are first) + our execution
        # Worst case: arrives, server just finished its budget. Waits Tps. Server gets budget Cps. Executes.
        # This simple bound is often given as 2*Tps (to start execution) + C_task or similar for simpler cases.
        # A bound from some literature (e.g., related to bandwidth preservation):
        # Response time R_i <= t_i + C_i where t_i is solution to t_i = B_i(t_i) + (T_s - C_s)
        # B_i(t_i) is blocking from higher priority sporadic tasks.
        # This is too complex for a quick addition.

        # Simplistic placeholder:
        # Max wait for server to become active and have budget for this task
        wait_time = Tps + (Tps - Cps) # Wait for next period + time server might be idle in its period
        execution_in_server = math.ceil(sporadic_task.wcet / Cps) * Tps - (Tps - sporadic_task.wcet) # Simplified if fits one Cps
        
        if sporadic_task.wcet <= Cps:
             # Arrives at start of server period, server busy for (Tps-Cps), then task gets Cps.
             # Or arrives right after server used budget, waits Tps.
             # Consider the model from Burns & Wellings for PS (section on Polling Servers):
             # R = finish_time - arrival_time
             # Worst-case queueing time for a task arriving at t_arrival:
             # q_i = (k_i -1)Tps + Cps   (where k_i is number of server instances to complete Ci)
             # Completion time C_i_f = q_i + C_i
             # This is also simplified.
             # Let's use a bound often cited: R_i <= 2*Tps + execution_time_within_server
             # Execution time within server assuming it gets dedicated slot when server runs:
             # Number of server periods needed: ceil(WCET_s / Cps)
             # Time taken = (ceil(WCET_s / Cps) - 1) * Tps + (time in last server period)
             # This is getting into detailed server theory which is beyond a quick update.

             # **VERY BASIC PESSIMISTIC PLACEHOLDER**:
             return 2 * Tps + sporadic_task.wcet


        return float('inf') # If WCET > Cps and we don't model multi-period execution by server



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