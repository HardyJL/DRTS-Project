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

        if not cores: # Handle case with no cores
            return components

        # Distribute components among cores
        components_per_core = [0] * self.config.num_cores
        for i in range(self.config.num_components):
            # Assign to the core with the fewest components, or round robin
            target_core_idx = i % self.config.num_cores # Simple round robin
            # target_core_idx = components_per_core.index(min(components_per_core)) # Fewest components
            components_per_core[target_core_idx] += 1

        # Generate component utilizations for each core
        core_component_utils = []
        for i in range(self.config.num_cores):
            if components_per_core[i] > 0:
                # Create random utilizations for components on this core
                # Ensure core_utils[i] is not too small for the number of components
                min_comp_util = 0.01 # Min util for a component
                max_comp_util = max(min_comp_util, core_utils[i] * 0.95) # Max util for a component

                if components_per_core[i] * min_comp_util > core_utils[i] and core_utils[i] > 0:
                     print(f"Warning: Core {cores[i]['core_id']} util {core_utils[i]:.2f} too low for {components_per_core[i]} components with min_util {min_comp_util}. Adjusting.")
                     # Heuristic: assign average util if sum of min_utils is too high
                     avg_util = core_utils[i] / components_per_core[i]
                     utils = [max(min_comp_util, avg_util * random.uniform(0.8,1.2)) for _ in range(components_per_core[i])]
                     # Normalize to ensure sum matches core_utils[i]
                     current_sum = sum(utils)
                     if current_sum > 0 :
                         utils = [u * core_utils[i] / current_sum for u in utils]
                     else: # If all somehow became zero, distribute evenly
                         utils = [core_utils[i]/components_per_core[i]] * components_per_core[i]

                elif core_utils[i] == 0 and components_per_core[i] > 0:
                    utils = [min_comp_util] * components_per_core[i] # Give small util if core util is 0
                else:
                    utils = randfixedsum(components_per_core[i], core_utils[i], nsets=1,
                                        minval=min_comp_util, maxval=max_comp_util)[0]
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
        component_idx_counter = 0
        for core_idx in range(self.config.num_cores):
            core = cores[core_idx]
            for i in range(components_per_core[core_idx]):
                if component_idx_counter >= self.config.num_components:
                    break # Should not happen if components_per_core sums correctly

                scheduler = core["scheduler"]

                # Set budget and period for the component itself (its BDR interface to the core)
                util = core_component_utils[core_idx][i]

                # Generate component's own budget and period
                # These represent the component's interface to the core scheduler
                # For simplicity, let's make component periods somewhat regular
                comp_period = random.randint(self.config.server_period_range[0] // 2, self.config.server_period_range[1] //2) * 2 # Even periods
                comp_period = max(10, comp_period) # Ensure a minimum component period
                comp_budget = max(1, round(util * comp_period))

                # Server parameters (will be empty if no sporadic tasks end up in this component)
                # We generate them here; if a component gets no sporadic tasks, these can be ignored or set to "" by writer.
                # For now, let's assume any component *might* host a server if sporadic_task_ratio > 0
                server_budget_val = ""
                server_period_val = ""

                # Decide if this component will host a server (e.g. if sporadic_task_ratio > 0).
                # A simpler approach: generate server params, task_generator will decide if they are used.
                # Let's make it so server params are only generated if config.sporadic_task_ratio > 0
                # and perhaps only for a subset of components to make it more interesting.
                # For now, let's generate for all, and task_generator can assign sporadic tasks.
                # The writer can then decide to write them or not.
                
                # Heuristic: Server parameters for the Polling Server within this component
                # These are NOT the component's own budget/period for its BDR interface with the core.
                # These are for the PS *inside* this component.
                current_server_period = random.randint(self.config.server_period_range[0],
                                                       self.config.server_period_range[1])
                budget_factor = random.uniform(self.config.server_budget_factor_range[0],
                                               self.config.server_budget_factor_range[1])
                current_server_budget = max(1, int(round(current_server_period * budget_factor)))

                # Assign server parameters to be stored with the component
                # These will be written to budgets.csv
                # The TaskGenerator will then know if a component is intended to have sporadic tasks served by these params
                server_budget_val = current_server_budget
                server_period_val = current_server_period


                priority = ""
                if core["scheduler"] == "RM": # Priority of the *component* on the core
                    # This needs to be determined relative to other components on the same core
                    # This should be set after all components for a core are known
                    pass # Will be set later

                component = {
                    "component_id": self.component_names[component_idx_counter],
                    "scheduler": scheduler, # Scheduler for tasks *within* this component
                    "budget": comp_budget,   # Component's budget from core (for BDR)
                    "period": comp_period,   # Component's period for core (for BDR)
                    "core_id": core["core_id"],
                    "priority": priority,    # Component's priority on the core if core is RM
                    "utilization": util,     # Target utilization for tasks *within* this component
                    "server_budget": server_budget_val, # Budget for the PS *inside* this component
                    "server_period": server_period_val  # Period for the PS *inside* this component
                }
                components.append(component)
                component_idx_counter += 1

        # Assign priorities to components if their core uses RM
        for core in cores:
            if core["scheduler"] == "RM":
                core_components = [comp for comp in components if comp["core_id"] == core["core_id"]]
                # Sort components by their period (shorter period = higher priority for RM)
                core_components.sort(key=lambda x: x["period"])
                for i, comp_data in enumerate(core_components):
                    # Find this component in the main list and update its priority
                    for c in components:
                        if c["component_id"] == comp_data["component_id"]:
                            c["priority"] = i # 0 is highest
                            break
        return components

    def adjust_schedulability(self, components: List[Dict[str, Any]],
                             tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Adjust task parameters to make the system schedulable or unschedulable.
        This is a placeholder and might need more sophisticated logic, especially with servers.
        """
        if self.config.schedulable:
            # Make system schedulable by ensuring utilization constraints for periodic tasks
            # And ensuring server utilization can cover sporadic task utilization
            for component in components:
                comp_periodic_tasks = [t for t in tasks if t["component_id"] == component["component_id"] and t.get("task_type", "periodic") == "periodic"]
                comp_sporadic_tasks = [t for t in tasks if t["component_id"] == component["component_id"] and t.get("task_type") == "sporadic"]

                if not comp_periodic_tasks and not comp_sporadic_tasks:
                    continue

                # Periodic tasks schedulability
                if comp_periodic_tasks:
                    scheduler = component["scheduler"]
                    if scheduler == "EDF":
                        task_utils = [t["wcet"] / t["period"] for t in comp_periodic_tasks]
                        total_util = sum(task_utils)
                        if total_util > 0.9:  # Target EDF utilization for periodic tasks
                            scale_factor = 0.9 / total_util if total_util > 0 else 1
                            for task in comp_periodic_tasks:
                                task_idx = tasks.index(task) # This might be inefficient
                                tasks[task_idx]["wcet"] = max(1, int(task["wcet"] * scale_factor))
                    elif scheduler == "RM":
                        n = len(comp_periodic_tasks)
                        if n > 0:
                            rm_bound = n * (2 ** (1/n) - 1)
                            task_utils = [t["wcet"] / t["period"] for t in comp_periodic_tasks]
                            total_util = sum(task_utils)
                            if total_util > rm_bound * 0.95:
                                scale_factor = (rm_bound * 0.95) / total_util if total_util > 0 else 1
                                for task in comp_periodic_tasks:
                                    task_idx = tasks.index(task)
                                    tasks[task_idx]["wcet"] = max(1, int(task["wcet"] * scale_factor))
                
                # Sporadic tasks and server capacity (very basic check)
                if comp_sporadic_tasks and component.get("server_budget") and component.get("server_period"):
                    server_util = component["server_budget"] / component["server_period"]
                    sporadic_util = sum(t["wcet"] / t["period"] for t in comp_sporadic_tasks) # period is MIT
                    
                    if sporadic_util > server_util * 0.9: # Ensure server util is enough
                        # This might require increasing server budget/period or reducing sporadic load
                        # For simplicity, this example doesn't auto-adjust server params here
                        # but one could scale down sporadic WCETs or increase server budget
                        print(f"Warning: Component {component['component_id']} server util {server_util:.2f} might be too low for sporadic util {sporadic_util:.2f}")


        else:  # Make unschedulable
            if components and tasks:
                component_to_mess_up = random.choice(components)
                comp_tasks = [t for t in tasks if t["component_id"] == component_to_mess_up["component_id"]]
                if comp_tasks:
                    scale_factor = 1.5  # Increase WCETs by 50%
                    for task in comp_tasks:
                        for i, t_main in enumerate(tasks):
                            if t_main["task_name"] == task["task_name"]:
                                tasks[i]["wcet"] = max(1, int(task["wcet"] * scale_factor))
                                break
        return tasks