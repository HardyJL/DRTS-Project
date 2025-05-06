"""
Core generation module for hierarchical taskset generator
"""
import random
import numpy as np
from typing import List, Dict, Any, Tuple


class CoreGenerator:
    """Generator for cores in hierarchical scheduling system"""
    
    def __init__(self, config):
        """
        Initialize the core generator
        
        Args:
            config: Configuration object with settings
        """
        self.config = config
    
    def generate_cores(self) -> List[Dict[str, Any]]:
        """
        Generate core definitions with varying speed factors.
        
        Returns:
            List of core dictionaries
        """
        cores = []
        for i in range(1, self.config.num_cores + 1):
            # Generate a random speed factor within the given range
            speed_factor = round(random.uniform(
                self.config.speed_factor_range[0], 
                self.config.speed_factor_range[1]), 
                2)
            
            # Alternate between EDF and RM for core schedulers
            scheduler = "EDF" if i % 2 == 0 else "RM"
            
            core = {
                "core_id": f"Core_{i}",
                "speed_factor": speed_factor,
                "scheduler": scheduler
            }
            cores.append(core)
        
        return cores
    
    def distribute_utilization(self, total_util: float, cores: List[Dict[str, Any]]) -> List[float]:
        """
        Distribute the total utilization among cores based on their speed factors.
        
        Args:
            total_util: Total system utilization (0-1)
            cores: List of core dictionaries
            
        Returns:
            List of core utilizations
        """
        # Calculate weight for each core based on speed factor
        speed_factors = np.array([core["speed_factor"] for core in cores])
        weights = speed_factors / np.sum(speed_factors)
        
        # Distribute utilization according to weights
        core_utils = weights * total_util
        
        return core_utils