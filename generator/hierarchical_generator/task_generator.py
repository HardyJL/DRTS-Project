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
        
        Args:
            config: Configuration object with settings
        """
        self.config = config
    
    def distribute_tasks(self, components: List[Dict[str, Any]]) -> List[int]:
        """
        Distribute tasks among components.
        
        Args:
            components: List of component dictionaries
            
        Returns:
            List containing the number of tasks per component
        """
        num_components = len(components)
        
        # Ensure minimum 1 task per component
        tasks_per_component = [1] * num_components
        remaining_tasks = self.config.num_tasks - num_components
        
        if remaining_tasks < 0:
            # If fewer tasks than components, some components will have no tasks
            tasks_per_component = [0] * num_components
            for i in range(self.config.num_tasks):
                tasks_per_component[i] = 1
        elif remaining_tasks > 0:
            # Distribute remaining tasks based on component utilization
            utils = np.array([comp["utilization"] for comp in components])
            weights = utils / np.sum(utils)
            
            # Initial distribution based on weights
            additional_tasks = np.zeros(num_components, dtype=int)
            for _ in range(remaining_tasks):
                # Pick a component with probability proportional to weight
                comp_idx = np.random.choice(num_components, p=weights)
                additional_tasks[comp_idx] += 1
            
            tasks_per_component = [1 + additional for additional in additional_tasks]
        
        return tasks_per_component
    
    def generate_tasks(self, components: List[Dict[str, Any]], 
                      tasks_per_component: List[int]) -> List[Dict[str, Any]]:
        """
        Generate tasks for each component.
        
        Args:
            components: List of component dictionaries
            tasks_per_component: List containing the number of tasks per component
            
        Returns:
            List of task dictionaries
        """
        tasks = []
        task_id = 0
        
        for comp_idx, component in enumerate(components):
            num_tasks = tasks_per_component[comp_idx]
            
            if num_tasks == 0:
                continue
            
            # Get component utilization
            comp_util = component["utilization"]
            
            # Generate task utilizations (relative to component)
            task_utils = randfixedsum(num_tasks, comp_util, nsets=1, 
                                     minval=0.01, maxval=min(0.9, comp_util))[0]
            
            # Generate periods
            periods = generate_periods(num_tasks, min_period=5, max_period=300)
            
            # Calculate WCETs
            wcets = calculate_wcet_from_utilization(task_utils, periods)
            
            # Create tasks
            for i in range(num_tasks):
                priority = ""
                if component["scheduler"] == "RM":
                    # RM priority based on period (shorter period -> higher priority)
                    priority = i  # We'll sort by period later
                
                task = {
                    "task_name": f"Task_{task_id}",
                    "wcet": wcets[i],
                    "period": periods[i],
                    "component_id": component["component_id"],
                    "priority": priority
                }
                
                tasks.append(task)
                task_id += 1
        
        # Sort tasks by period within each RM component for proper RM priority assignment
        for component in components:
            if component["scheduler"] == "RM":
                # Get tasks for this component
                comp_tasks = [task for task in tasks if task["component_id"] == component["component_id"]]
                
                if comp_tasks:
                    # Sort by period (ascending)
                    comp_tasks.sort(key=lambda x: x["period"])
                    
                    # Assign priorities (0 = highest priority)
                    for i, task in enumerate(comp_tasks):
                        # Find this task in the main list and update its priority
                        for t in tasks:
                            if t["task_name"] == task["task_name"]:
                                t["priority"] = i
                                break
        
        return tasks
    