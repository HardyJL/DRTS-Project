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
        # ... (keep this function as is, it just distributes the total number of tasks) ...
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
        """
        Generate tasks for each component, considering server parameters if present.
        """
        tasks = []
        task_id_counter = 0

        for comp_idx, component in enumerate(components):
            num_tasks_total_for_comp = tasks_per_component[comp_idx]
            if num_tasks_total_for_comp == 0:
                continue

            component_target_util = max(0.01, component.get("utilization", 0.01))
            
            # Server parameters from the component dictionary
            server_budget = component.get("server_budget")
            server_period = component.get("server_period")
            
            server_util_reserved = 0
            if server_budget and server_period and server_period > 0:
                server_util_reserved = server_budget / server_period

            # Available utilization for purely periodic tasks
            util_for_periodic_tasks = component_target_util - server_util_reserved
            if util_for_periodic_tasks < 0: # Server needs more than component has
                util_for_periodic_tasks = 0 # No room for periodic tasks
                # Potentially adjust server_util_reserved if it exceeds component_target_util
                if server_util_reserved > component_target_util:
                    server_util_reserved = component_target_util # Cap server util
                    print(f"Warning: Server utilization for {component['component_id']} capped to component util {component_target_util:.2f}")


            num_sporadic_tasks = int(round(num_tasks_total_for_comp * self.config.sporadic_task_ratio))
            num_periodic_tasks = num_tasks_total_for_comp - num_sporadic_tasks

            # Ensure server is only "active" if there are sporadic tasks to generate for it
            if num_sporadic_tasks == 0:
                server_util_reserved = 0 # No sporadic tasks, no server util needed from component's budget
                util_for_periodic_tasks = component_target_util # All component util for periodic

            # Generate PERIODIC tasks
            if num_periodic_tasks > 0 and util_for_periodic_tasks > 0.001 : # Ensure there's some util for them
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
            elif num_periodic_tasks > 0 : # Not enough util for this many periodic, generate with minimal util
                 for _ in range(num_periodic_tasks):
                    p = random.randint(20,500)
                    tasks.append({
                        "task_name": f"Task_{task_id_counter}", "wcet": 1,
                        "period": p, "component_id": component["component_id"],
                        "priority": "", "task_type": "periodic", "deadline": p
                    })
                    task_id_counter +=1


            # Generate SPORADIC tasks (to be served by the component's server)
            if num_sporadic_tasks > 0 and server_util_reserved > 0.001: # Ensure server has some capacity
                min_task_u = 0.001
                # Sporadic tasks' total utilization should fit within server_util_reserved
                task_utils_sporadic = randfixedsum(num_sporadic_tasks, server_util_reserved, nsets=1,
                                                   minval=min_task_u, maxval=max(min_task_u, server_util_reserved * 0.95))[0]
                # MITs for sporadic tasks, can be different range
                mits_sporadic = generate_periods(num_sporadic_tasks, min_period=30, max_period=600)
                wcets_sporadic = calculate_wcet_from_utilization(task_utils_sporadic, mits_sporadic)

                for i in range(num_sporadic_tasks):
                    min_df, max_df = self.config.sporadic_deadline_factor_range
                    deadline_factor = random.uniform(min_df, max_df)
                    deadline = int(round(mits_sporadic[i] * deadline_factor))
                    deadline = max(wcets_sporadic[i], deadline) # Deadline >= WCET
                    deadline = min(mits_sporadic[i], deadline)   # Deadline <= MIT

                    tasks.append({
                        "task_name": f"Task_{task_id_counter}", "wcet": wcets_sporadic[i],
                        "period": mits_sporadic[i], # This is MIT
                        "component_id": component["component_id"],
                        "priority": "", "task_type": "sporadic", "deadline": deadline
                    })
                    task_id_counter += 1
            elif num_sporadic_tasks > 0: # Not enough server util, generate minimal sporadic tasks
                for _ in range(num_sporadic_tasks):
                    mit = random.randint(30,600)
                    wcet = 1
                    deadline = random.randint(wcet, mit)
                    tasks.append({
                        "task_name": f"Task_{task_id_counter}", "wcet": wcet,
                        "period": mit, "component_id": component["component_id"],
                        "priority": "", "task_type": "sporadic", "deadline": deadline
                    })
                    task_id_counter +=1


        # Assign RM priorities if component uses RM
        # This priority applies to periodic tasks and potentially servers (if modeled as tasks)
        for component in components:
            if component["scheduler"] == "RM":
                comp_tasks_for_rm_sorting = [
                    t for t in tasks if t["component_id"] == component["component_id"] and t["task_type"] == "periodic"
                ]
                # If servers were explicitly modeled as tasks, they would be included here too.
                # For now, sporadic tasks are not directly RM scheduled in this simple model.

                if comp_tasks_for_rm_sorting:
                    comp_tasks_for_rm_sorting.sort(key=lambda x: x["period"])
                    for i, sorted_task_details in enumerate(comp_tasks_for_rm_sorting):
                        for task_in_main_list in tasks:
                            if task_in_main_list["task_name"] == sorted_task_details["task_name"]:
                                task_in_main_list["priority"] = i
                                break
        return tasks