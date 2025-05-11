import os
import sys
import csv
import math
from typing import List, Dict, Tuple, Optional, Union, Any
from functools import reduce
from core import Core, Component, Task, Solution
from csv_functions import load_models_from_csv, write_solutions_to_csv, lcm_of_list

# Define the Bounded Delay Resource (BDR) model
# This model is used for hierarchical scheduling analysis.
class BDRModel:
    """
    Implementation of the Bounded Delay Resource (BDR) model for hierarchical scheduling.
    Based on Section 3.3 of the "Hierarchical Scheduling" chapter.
    """
    
    def __init__(self, alpha: float, delta: float):
        """
        Initialize a BDR model with availability factor alpha and partition delay delta.
        
        Args:
            alpha: Availability factor (0 < alpha <= 1)
            delta: Partition delay (delta >= 0)
        """
        # Validate and store parameters
        self.alpha = min(max(alpha, 0.01), 1.0)  # Cap alpha between 0.01 and 1.0
        self.delta = max(delta, 0.0)  # Ensure delta is non-negative
    
    @classmethod
    def from_srp_model(cls, srp_gamma: List[Tuple[float, float]], srp_period: float) -> 'BDRModel':
        """
        Create a BDR model from a Static Resource Partition (SRP) model.
        Based on Section 3.3.2 of the chapter.
        
        Args:
            srp_gamma: List of (start, end) time pairs representing resource availability
            srp_period: The partition period
            
        Returns:
            A BDR model instance
        """
        # Calculate availability factor (Definition 2)
        total_available_time = sum(end - start for start, end in srp_gamma)
        alpha = total_available_time / srp_period if srp_period > 0 else 0
        
        # Calculate partition delay (Definition 3)
        if not srp_gamma or alpha <= 0:
            delta = srp_period  # Worst case
        else:
            # Use a simpler formula based on the half-half algorithm
            # from Theorem 3 (often used in practice)
            delta = 2 * srp_period * (1 - alpha)
        
        return cls(alpha, delta)
    
    @classmethod
    def from_periodic_resource(cls, budget: float, period: float) -> 'BDRModel':
        """
        Create a BDR model from a periodic resource model with budget and period.
        
        Args:
            budget: Resource budget
            period: Resource period
            
        Returns:
            A BDR model instance
        """
        # Handle the case where budget ≥ period (full utilization)
        if budget >= period:
            return cls(1.0, 0.0)
        
        # Calculate availability factor (alpha) from budget and period
        alpha = budget / period
        
        # Calculate partition delay using the formula from the half-half algorithm
        delta = 2 * period * (1 - alpha)
        
        return cls(alpha, delta)
    
    def to_periodic_resource(self) -> Tuple[float, float]:
        """
        Convert this BDR model to a periodic resource model using the half-half algorithm.
        Based on Theorem 3 from Section 3.3.3.
        
        Returns:
            Tuple of (budget, period)
        """
        if self.alpha >= 1.0:
            # Full utilization case
            return 1.0, 1.0
        
        # Apply the half-half algorithm from Theorem 3
        period = self.delta / (2 * (1 - self.alpha))
        budget = self.alpha * period
        
        return budget, period
    
    def supply_bound_function(self, t: float) -> float:
        """
        Calculate the supply bound function (SBF) for this BDR model.
        Based on Equation 6 from Section 3.3.2.
        
        Args:
            t: Time interval
            
        Returns:
            Minimum resource supply in the interval [0, t]
        """
        if t >= self.delta:
            return self.alpha * (t - self.delta)
        else:
            return 0.0
    
    def is_schedulable_with_dbf(self, dbf_values: Dict[float, float]) -> bool:
        """
        Check if a workload is schedulable under this BDR model
        by comparing demand bound function and supply bound function.
        
        Args:
            dbf_values: Dictionary mapping time points to DBF values
            
        Returns:
            True if schedulable, False otherwise
        """
        for t, demand in dbf_values.items():
            supply = self.supply_bound_function(t)
            if demand > supply:
                return False
        
        return True
    
    def is_schedulable_edf_workload(self, tasks: List[Task]) -> bool:
        """
        Check if a workload scheduled by EDF is schedulable under this BDR model.
        Based on Section 3.3.3.
        
        Args:
            tasks: List of Task objects
            
        Returns:
            True if schedulable, False otherwise
        """
        if not tasks:
            return True  # Empty task set is trivially schedulable
        
        # Check utilization first
        total_utilization = sum(float(task.wcet) / float(task.period) for task in tasks)
        if total_utilization > self.alpha:
            return False  # Not schedulable due to utilization bound
        
        # Calculate hyperperiod
        periods = [int(task.period) for task in tasks]
        hyperperiod = lcm_of_list(periods)
        
        # Check schedulability at all relevant time points
        time_points = set()
        for task in tasks:
            period = int(task.period)
            for i in range(1, hyperperiod // period + 1):
                time_points.add(i * period)
        
        for t in sorted(time_points):
            # Calculate EDF demand bound function (Equation 2)
            demand = sum(float(task.wcet) * math.floor(t / float(task.period)) for task in tasks)
            supply = self.supply_bound_function(t)
            
            if demand > supply:
                return False  # Not schedulable at this time point
        
        return True  # Schedulable at all time points
    
    def is_schedulable_rm_task(self, task: Task, all_tasks: List[Task]) -> bool:
        """
        Check if a specific task scheduled by RM is schedulable under this BDR model.
        Based on Theorem 5 from Section 3.3.3.
        
        Args:
            task: The task to check
            all_tasks: All tasks in the component
            
        Returns:
            True if the task is schedulable, False otherwise
        """
        wcet = float(task.wcet)
        period = float(task.period)
        
        # Get higher priority tasks
        higher_priority_tasks = []
        for other_task in all_tasks:
            if other_task.task_name != task.task_name:
                # In RM, lower number priority means higher priority
                # If no priority is specified, use period (shorter period = higher priority)
                if task.priority is not None and other_task.priority is not None:
                    if other_task.priority < task.priority:
                        higher_priority_tasks.append(other_task)
                elif float(other_task.period) < float(task.period):
                    higher_priority_tasks.append(other_task)
        
        # Define time points to check
        time_points = set([int(period)])  # Always check at the period
        
        # Add key intermediate points, especially around delta
        step = max(1, int(period) // 50)  # Check at least 50 points within period
        for t in range(max(1, int(self.delta) - 10), int(period) + 1, step):
            time_points.add(t)
        
        # Add task release points (multiples of higher priority task periods)
        for hp_task in higher_priority_tasks:
            hp_period = float(hp_task.period)
            for i in range(1, int(period / hp_period) + 2):
                time_points.add(int(i * hp_period))
        
        # Add points just after delta
        if self.delta > 0:
            time_points.add(int(self.delta) + 1)
            time_points.add(int(self.delta) + 2)
        
        # Check all time points
        for t in sorted(time_points):
            if t > period:  # Don't check beyond period
                break
                
            # Calculate RM demand bound function for this task (Equation 4)
            demand = wcet  # The task's own demand
            
            # Add interference from higher priority tasks
            for hp_task in higher_priority_tasks:
                hp_wcet = float(hp_task.wcet)
                hp_period = float(hp_task.period)
                demand += math.ceil(t / hp_period) * hp_wcet
            
            # Check against supply
            supply = self.supply_bound_function(t)
            
            if demand <= supply:
                return True  # Found a time point where demand <= supply
        
        return False  # No time point found where demand <= supply
    
    def is_schedulable_rm_workload(self, tasks: List[Task]) -> bool:
        """
        Check if all tasks in a workload scheduled by RM are schedulable under this BDR model.
        
        Args:
            tasks: List of Task objects
            
        Returns:
            True if all tasks are schedulable, False otherwise
        """
        if not tasks:
            return True  # Empty task set is trivially schedulable
        
        # Sort tasks by priority if available, otherwise by period (RM default)
        if all(task.priority is not None for task in tasks):
            # Sort by explicit priority (lower number = higher priority)
            sorted_tasks = sorted(tasks, key=lambda x: float(x.priority) if x.priority is not None else float('inf'))
        else:
            # Sort by period (RM default - shorter period = higher priority)
            sorted_tasks = sorted(tasks, key=lambda x: float(x.period))
        
        # Check each task
        schedulable_tasks = []
        for task in sorted_tasks:
            if self.is_schedulable_rm_task(task, tasks):
                schedulable_tasks.append(task.task_name)
        
        return len(schedulable_tasks) == len(tasks)
    
    def get_schedulable_tasks_rm(self, tasks: List[Task]) -> Dict[str, bool]:
        """
        Get the schedulability status of each task in a RM workload.
        
        Args:
            tasks: List of Task objects
            
        Returns:
            Dictionary mapping task names to schedulability status
        """
        result = {}
        for task in tasks:
            result[task.task_name] = self.is_schedulable_rm_task(task, tasks)
        return result
    
    def get_schedulable_tasks_edf(self, tasks: List[Task]) -> Dict[str, bool]:
        """
        Get the schedulability status of each task in an EDF workload.
        In EDF, either all tasks are schedulable or none are.
        
        Args:
            tasks: List of Task objects
            
        Returns:
            Dictionary mapping task names to schedulability status
        """
        is_schedulable = self.is_schedulable_edf_workload(tasks)
        return {task.task_name: is_schedulable for task in tasks}
    
    @staticmethod
    def check_theorem1_schedulability(parent_bdr: 'BDRModel', children_bdr: List['BDRModel']) -> bool:
        """
        Check schedulability based on Theorem 1 from Section 3.3.3.
        
        Args:
            parent_bdr: The parent BDR model
            children_bdr: List of child BDR models
            
        Returns:
            True if schedulable according to Theorem 1, False otherwise
        """
        # Check sum of availability factors
        total_alpha = sum(child.alpha for child in children_bdr)
        if total_alpha > parent_bdr.alpha:
            return False
        
        # Check each partition delay
        for child in children_bdr:
            # Special case: If both parent and child have Δ = 0, consider it valid
            # This happens when both have full resource availability (α = 1.0)
            if child.delta == 0 and parent_bdr.delta == 0:
                continue
                
            if child.delta <= parent_bdr.delta:
                return False
        
        return True
    
    def __str__(self) -> str:
        """String representation of the BDR model."""
        return f"BDR(α={self.alpha:.4f}, Δ={self.delta:.4f})"



