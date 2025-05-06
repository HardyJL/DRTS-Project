"""
Component generation module for hierarchical taskset generator
"""
import random
import numpy as np
from typing import List, Dict, Any
from .utils import randfixedsum


class ComponentGenerator:
    """Generator for components in hierarchical scheduling system"""
    
    def __init__(self, config):
        """
        Initialize the component generator
        
        Args:
            config: Configuration object with settings
        """
        self.config = config
        # Component names available for generation
        self.component_names = [
            "Camera_Sensor", "Image_Processor", "Bitmap_Processor", "Lidar_Sensor",
            "Control_Unit", "GPS_Sensor", "Communication_Unit", "Proximity_Sensor", 
            "Radar_Sensor", "Sonar_Sensor", "Laser_Sensor", "Infrared_Sensor",
            "Ultraviolet_Sensor", "Thermal_Sensor", "Pressure_Sensor", "Humidity_Sensor",
            "Temperature_Sensor", "Light_Sensor", "Sound_Sensor", "Vibration_Sensor",
            "Motion_Sensor", "Acceleration_Sensor", "Gyroscope_Sensor", "Magnetometer_Sensor",
            "Compass_Sensor", "Altimeter_Sensor", "Barometer_Sensor", "Hygrometer_Sensor",
            "Anemometer_Sensor", "Rain_Gauge_Sensor", "Snow_Gauge_Sensor", "Thermometer_Sensor"
        ]
    
    def generate_components(self, cores: List[Dict[str, Any]], 
                           core_utils: List[float]) -> List[Dict[str, Any]]:
        """
        Generate component definitions and distribute them among cores.
        
        Args:
            cores: List of core dictionaries
            core_utils: List of core utilizations
            
        Returns:
            List of component dictionaries
        """
        components = []
        
        # Distribute components among cores
        components_per_core = [0] * self.config.num_cores
        for i in range(self.config.num_components):
            # Assign to the core with the fewest components
            target_core_idx = components_per_core.index(min(components_per_core))
            components_per_core[target_core_idx] += 1
        
        # Generate component utilizations for each core
        core_component_utils = []
        for i in range(self.config.num_cores):
            if components_per_core[i] > 0:
                # Create random utilizations for components on this core
                utils = randfixedsum(components_per_core[i], core_utils[i], nsets=1, 
                                    minval=0.05, maxval=min(0.9, core_utils[i]))[0]
                core_component_utils.append(utils)
            else:
                core_component_utils.append([])
        
        # Ensure we have enough names
        if self.config.num_components > len(self.component_names):
            for i in range(len(self.component_names), self.config.num_components):
                self.component_names.append(f"Component_{i+1}")
        
        # Shuffle the names
        random.shuffle(self.component_names)
        
        # Create components
        component_idx = 0
        for core_idx in range(self.config.num_cores):
            core = cores[core_idx]
            for i in range(components_per_core[core_idx]):
                # Choose a scheduler (if core is RM, all components must be RM or EDF)
                if core["scheduler"] == "RM":
                    scheduler = random.choice(["RM", "EDF"])
                else:
                    scheduler = "EDF"  # If core is EDF, all components must be EDF
                
                # Set budget and period
                util = core_component_utils[core_idx][i]
                
                # Generate budget and period such that budget/period approx. equals utilization
                period = random.randint(5, 40)  # Component period
                budget = max(1, round(util * period))  # Component budget
                
                # Set priority (only needed for RM scheduling at core level)
                priority = ""
                if core["scheduler"] == "RM":
                    priority = i  # Lower value means higher priority
                
                component = {
                    "component_id": self.component_names[component_idx],
                    "scheduler": scheduler,
                    "budget": budget,
                    "period": period,
                    "core_id": core["core_id"],
                    "priority": priority,
                    "utilization": util  # Store for task generation (not in actual format)
                }
                
                components.append(component)
                component_idx += 1
        
        return components
    
    def adjust_schedulability(self, components: List[Dict[str, Any]], 
                             tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Adjust task parameters to make the system schedulable or unschedulable.
        
        Args:
            components: List of component dictionaries
            tasks: List of task dictionaries
            
        Returns:
            Updated tasks
        """
        if self.config.schedulable:
            # Make system schedulable by ensuring utilization constraints
            for component in components:
                comp_tasks = [t for t in tasks if t["component_id"] == component["component_id"]]
                
                if not comp_tasks:
                    continue
                
                scheduler = component["scheduler"]
                
                if scheduler == "EDF":
                    # For EDF, ensure sum of utilizations <= 1
                    task_utils = [t["wcet"] / t["period"] for t in comp_tasks]
                    total_util = sum(task_utils)
                    
                    if total_util > 0.9:  # Leave some margin
                        # Scale down WCETs
                        scale_factor = 0.9 / total_util
                        for task in comp_tasks:
                            task_idx = tasks.index(task)
                            tasks[task_idx]["wcet"] = max(1, int(task["wcet"] * scale_factor))
                
                elif scheduler == "RM":
                    # For RM, use utilization bound: U <= n(2^(1/n) - 1)
                    n = len(comp_tasks)
                    if n > 0:
                        rm_bound = n * (2 ** (1/n) - 1)
                        task_utils = [t["wcet"] / t["period"] for t in comp_tasks]
                        total_util = sum(task_utils)
                        
                        if total_util > rm_bound * 0.95:  # Leave some margin
                            # Scale down WCETs
                            scale_factor = rm_bound * 0.95 / total_util
                            for task in comp_tasks:
                                task_idx = tasks.index(task)
                                tasks[task_idx]["wcet"] = max(1, int(task["wcet"] * scale_factor))
        
        else:  # Make unschedulable
            # Pick a random component and increase its tasks' WCETs
            if components:
                component = random.choice(components)
                comp_tasks = [t for t in tasks if t["component_id"] == component["component_id"]]
                
                if comp_tasks:
                    # Increase WCETs to exceed schedulability bounds
                    scale_factor = 1.5  # Increase by 50%
                    for task in comp_tasks:
                        task_idx = tasks.index(task)
                        tasks[task_idx]["wcet"] = max(1, int(task["wcet"] * scale_factor))
        
        return tasks