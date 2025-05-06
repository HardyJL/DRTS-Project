"""
Utility functions for hierarchical taskset generator
"""
import random
import numpy as np
from typing import List


def randfixedsum(n: int, u: float, nsets: int = 1, minval: float = 0.001, maxval: float = 0.999) -> np.ndarray:
    """
    Generate random sets of values with a fixed sum.
    
    Based on the RandFixedSum algorithm by Paul Emberson et al.
    
    Args:
        n: Number of values in each set
        u: Target sum of each set
        nsets: Number of sets to generate
        minval: Minimum value allowed
        maxval: Maximum value allowed
        
    Returns:
        A numpy array of shape (nsets, n) containing the random values
    """
    if n <= 0 or u < 0 or nsets <= 0 or minval < 0 or maxval <= minval:
        raise ValueError("Invalid parameters for randfixedsum")
        
    # Scale the sum to [0, n]
    s = u
    
    if s > n * maxval or s < n * minval:
        raise ValueError(f"Sum {s} is outside the feasible range [{n * minval}, {n * maxval}]")
    
    # Generate random points in the simplex
    t = np.random.random((nsets, n-1))
    t = np.sort(t, axis=1)
    t = np.column_stack((np.zeros((nsets, 1)), t, np.ones((nsets, 1))))
    diff = np.diff(t, axis=1)
    
    # Scale values to the desired sum and range
    diff = diff * s / np.sum(diff, axis=1, keepdims=True)
    
    # Constrain values to [minval, maxval]
    if minval > 0 or maxval < 1:
        for i in range(nsets):
            valid = False
            attempts = 0
            while not valid and attempts < 1000:
                diff_i = diff[i]
                if np.all(diff_i >= minval) and np.all(diff_i <= maxval):
                    valid = True
                else:
                    # Regenerate this set
                    t_i = np.random.random(n-1)
                    t_i = np.sort(t_i)
                    t_new = np.concatenate(([0], t_i, [1]))
                    diff_i = np.diff(t_new)
                    diff_i = diff_i * s / np.sum(diff_i)
                    diff[i] = diff_i
                attempts += 1
            
            if not valid:
                # If we can't generate a valid set, fallback to an even distribution
                diff[i] = np.ones(n) * s / n
                # Adjust to stay within bounds
                diff[i] = np.clip(diff[i], minval, maxval)
                # Normalize to ensure sum is s
                diff[i] = diff[i] * s / np.sum(diff[i])
    
    return diff


def generate_periods(n: int, min_period: int = 10, max_period: int = 1000, 
                    harmonic_ratio: float = 0.5) -> List[int]:
    """
    Generate task periods, with some being harmonic.
    
    Args:
        n: Number of periods to generate
        min_period: Minimum period value
        max_period: Maximum period value
        harmonic_ratio: Ratio of tasks with harmonic periods
        
    Returns:
        List of periods
    """
    # Base periods (powers of 2 or small primes multiplied by powers of 2)
    base_periods = [
        25, 50, 100, 200, 400, 800,  # Powers of 2 * 25
        30, 60, 120, 240, 480, 960,  # Powers of 2 * 30
        75, 150, 300, 600,           # Powers of 2 * 75
        10, 20, 40, 80, 160, 320     # Powers of 2 * 10
    ]
    
    # Filter base periods to be within range
    valid_base_periods = [p for p in base_periods if min_period <= p <= max_period]
    
    if not valid_base_periods:
        # If no valid base periods, create some
        valid_base_periods = [min_period * (2 ** i) for i in range(10) 
                             if min_period * (2 ** i) <= max_period]
    
    # Decide how many harmonic periods to generate
    n_harmonic = int(n * harmonic_ratio)
    n_random = n - n_harmonic
    
    # Generate harmonic periods
    harmonic_periods = []
    for _ in range(n_harmonic):
        harmonic_periods.append(random.choice(valid_base_periods))
    
    # Generate random periods
    random_periods = []
    for _ in range(n_random):
        period = random.randint(min_period, max_period)
        random_periods.append(period)
    
    periods = harmonic_periods + random_periods
    random.shuffle(periods)
    
    return periods


def calculate_wcet_from_utilization(utilizations: np.ndarray, periods: List[int]) -> List[int]:
    """
    Calculate Worst-Case Execution Times (WCET) from utilizations and periods.
    
    Args:
        utilizations: Array of task utilizations
        periods: List of task periods
        
    Returns:
        List of WCETs
    """
    wcets = []
    for util, period in zip(utilizations, periods):
        # WCET = Utilization * Period
        wcet = round(util * period)
        # Ensure WCET is at least 1
        wcet = max(1, wcet)
        wcets.append(wcet)
    
    return wcets