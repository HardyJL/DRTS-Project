"""
Task generation module for hierarchical taskset generator
"""
import random
import numpy as np
from typing import List, Dict, Any
from .utils import randfixedsum, generate_periods, calculate_wcet_from_utilization


class TaskGenerator:
    """Generator for tasks in hierarchical scheduling system"""

    def __init__(self, config):
        """
        Initialize the task generator
        """
        self.config = config

    def distribute_tasks(self, components: List[Dict[str, Any]]) -> List[int]:
        num_components = len(components)
        if num_components == 0:
            return []

        if self.config.num_tasks < num_components:
            tasks_per_component = [0] * num_components
            for i in range(self.config.num_tasks):
                tasks_per_component[i % num_components] += 1
            return tasks_per_component

        tasks_per_component = [1] * num_components
        remaining_tasks = self.config.num_tasks - num_components

        if remaining_tasks > 0:
            utils = np.array([max(0.001, comp.get("utilization", 0.01)) for comp in components])
            sum_utils = np.sum(utils)
            if sum_utils > 0:
                weights = utils / sum_utils
            else:
                weights = np.ones(num_components) / num_components
            
            additional_tasks = np.zeros(num_components, dtype=int)
            for _ in range(remaining_tasks):
                comp_idx = np.random.choice(num_components, p=weights)
                additional_tasks[comp_idx] += 1
            tasks_per_component = [tasks_per_component[i] + additional_tasks[i] for i in range(num_components)]
        return tasks_per_component


    def generate_tasks(self, components: List[Dict[str, Any]],
                      tasks_per_component: List[int]) -> List[Dict[str, Any]]:
        tasks = []
        task_id_counter = 0

        for comp_idx, component in enumerate(components):
            num_tasks_total_for_comp = tasks_per_component[comp_idx]
            if num_tasks_total_for_comp == 0:
                continue

            component_target_util = max(0.01, component.get("utilization", 0.01))
            
            server_budget_cps = component.get("server_budget")
            server_period_tps = component.get("server_period")
            
            server_util_reserved = 0
            # Ensure server_budget_cps and server_period_tps are valid numbers if they exist
            if isinstance(server_budget_cps, (int, float)) and \
               isinstance(server_period_tps, (int, float)) and server_period_tps > 0:
                server_util_reserved = server_budget_cps / server_period_tps
            else: # If server params are not valid, treat as no server budget/period
                server_budget_cps = None 
                server_period_tps = None

            util_for_periodic_tasks = component_target_util - server_util_reserved
            if util_for_periodic_tasks < 0:
                util_for_periodic_tasks = 0
                if server_util_reserved > component_target_util:
                    server_util_reserved = component_target_util
                    if server_period_tps and server_period_tps > 0 : # Recalculate Cps if Tps is valid
                        server_budget_cps = server_util_reserved * server_period_tps
                        component["server_budget"] = server_budget_cps # Update component dict if changed
                        print(f"Warning: Server budget for {component['component_id']} adjusted to {server_budget_cps:.2f} due to component util cap.")
                    else: # Cannot recalculate Cps if Tps is invalid
                        server_budget_cps = None 
                    print(f"Warning: Server utilization for {component['component_id']} capped to component util {component_target_util:.2f}")

            num_sporadic_tasks = int(round(num_tasks_total_for_comp * self.config.sporadic_task_ratio))
            num_periodic_tasks = num_tasks_total_for_comp - num_sporadic_tasks

            if num_sporadic_tasks == 0: # No sporadic tasks means no server util is consumed from component budget
                server_util_reserved = 0
                util_for_periodic_tasks = component_target_util
                server_budget_cps = None # Mark as no server effectively
                server_period_tps = None

            # Generate PERIODIC tasks
            if num_periodic_tasks > 0:
                if util_for_periodic_tasks > 0.001 :
                    min_task_u = 0.001
                    task_utils_periodic = randfixedsum(num_periodic_tasks, util_for_periodic_tasks, nsets=1,
                                                       minval=min_task_u, maxval=max(min_task_u, util_for_periodic_tasks * 0.95))[0]
                    periods_periodic = generate_periods(num_periodic_tasks, min_period=20, max_period=500)
                    wcets_periodic = calculate_wcet_from_utilization(task_utils_periodic, periods_periodic)

                    for i in range(num_periodic_tasks):
                        tasks.append({
                            "task_name": f"Task_{task_id_counter}", "wcet": wcets_periodic[i],
                            "period": periods_periodic[i], "component_id": component["component_id"],
                            "priority": "", "task_type": "periodic", "deadline": periods_periodic[i]
                        })
                        task_id_counter += 1
                else: # Not enough util for this many periodic, generate with minimal util
                     for _ in range(num_periodic_tasks):
                        p = random.randint(20,500)
                        tasks.append({
                            "task_name": f"Task_{task_id_counter}", "wcet": 1,
                            "period": p, "component_id": component["component_id"],
                            "priority": "", "task_type": "periodic", "deadline": p
                        })
                        task_id_counter +=1

            # Generate SPORADIC tasks
            if num_sporadic_tasks > 0:
                if server_util_reserved > 0.001 and server_budget_cps is not None and server_budget_cps >=1:
                    min_task_u_sporadic = 0.001
                    # Ensure maxval for randfixedsum is not less than minval
                    max_sporadic_task_util = max(min_task_u_sporadic, server_util_reserved * 0.95)

                    task_utils_sporadic = randfixedsum(num_sporadic_tasks, server_util_reserved, nsets=1,
                                                       minval=min_task_u_sporadic, 
                                                       maxval=max_sporadic_task_util)[0]
                    mits_sporadic = generate_periods(num_sporadic_tasks, min_period=30, max_period=600)
                    wcets_sporadic_initial = calculate_wcet_from_utilization(task_utils_sporadic, mits_sporadic)

                    for i in range(num_sporadic_tasks):
                        wcet_s = wcets_sporadic_initial[i]
                        mit_s = mits_sporadic[i]

                        # *** MODIFICATION FOR SCHEDULABLE CASE ***
                        if self.config.schedulable and server_budget_cps is not None:
                            if wcet_s > server_budget_cps:
                                print(f"  AdjustLOG: Sporadic Task_{task_id_counter} WCET {wcet_s} > Cps {server_budget_cps} for Comp {component['component_id']}. Clamping WCET.")
                                wcet_s = server_budget_cps # Cap WCET at server_budget
                            if wcet_s == 0 : wcet_s = 1 # Ensure wcet is at least 1

                        min_df, max_df = self.config.sporadic_deadline_factor_range
                        deadline_factor = random.uniform(min_df, max_df)
                        deadline = int(round(mit_s * deadline_factor))
                        deadline = max(wcet_s, deadline)
                        deadline = min(mit_s, deadline)

                        tasks.append({
                            "task_name": f"Task_{task_id_counter}", "wcet": wcet_s,
                            "period": mit_s, # This is MIT
                            "component_id": component["component_id"],
                            "priority": "", "task_type": "sporadic", "deadline": deadline
                        })
                        task_id_counter += 1
                else: # Not enough server util or invalid server params, generate minimal sporadic tasks
                    for _ in range(num_sporadic_tasks):
                        mit = random.randint(30,600)
                        wcet = 1
                        # Ensure WCET is capped by server budget if schedulable and server_budget is sensible
                        if self.config.schedulable and isinstance(server_budget_cps, (int,float)) and server_budget_cps > 0:
                            wcet = min(wcet, server_budget_cps)
                        
                        deadline = random.randint(wcet, mit)
                        tasks.append({
                            "task_name": f"Task_{task_id_counter}", "wcet": wcet,
                            "period": mit, "component_id": component["component_id"],
                            "priority": "", "task_type": "sporadic", "deadline": deadline
                        })
                        task_id_counter +=1
        
        # Assign RM priorities for periodic tasks in RM components
        for component in components:
            if component["scheduler"] == "RM":
                comp_tasks_for_rm_sorting = [
                    t for t in tasks if t["component_id"] == component["component_id"] and t["task_type"] == "periodic"
                ]
                if comp_tasks_for_rm_sorting:
                    comp_tasks_for_rm_sorting.sort(key=lambda x: x["period"])
                    for i, sorted_task_details in enumerate(comp_tasks_for_rm_sorting):
                        for task_in_main_list in tasks:
                            if task_in_main_list["task_name"] == sorted_task_details["task_name"]:
                                task_in_main_list["priority"] = i
                                break
        return tasks