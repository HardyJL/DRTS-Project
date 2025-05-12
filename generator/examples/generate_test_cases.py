#!/usr/bin/env python3
"""
Example script demonstrating how to use the hierarchical taskset generator
to create a suite of test cases with different characteristics.
"""

import os
import sys
import random

# Add parent directory to path to import generator package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hierarchical_generator.config import Config
from hierarchical_generator.core_generator import CoreGenerator
from hierarchical_generator.component_generator import ComponentGenerator
from hierarchical_generator.task_generator import TaskGenerator
from hierarchical_generator.writer import CSVWriter


def generate_test_case(name, num_cores, num_components, num_tasks,
                      utilization, schedulable=True, speed_range=(0.5, 1.5),
                      sporadic_ratio=0.0, # New parameter, default to 0
                      sporadic_deadline_range=(0.7, 1.0), # New parameter
                      seed=None):
    """Generate a single test case with the given parameters."""
    # Set up configuration
    config = Config() # Initializes with defaults
    config.num_cores = num_cores
    config.num_components = num_components
    config.num_tasks = num_tasks
    config.utilization = utilization
    config.output_dir = "Generated_Test_Cases" # Consistent with previous
    config.test_case_name = name
    config.speed_factor_range = speed_range
    config.schedulable = schedulable
    config.seed = seed
    config.sporadic_task_ratio = sporadic_ratio # Set from function argument
    config.sporadic_deadline_factor_range = sporadic_deadline_range # Set from function argument

    # Print config being used for this specific test case generation
    print(f"\n--- Generating Test Case: {name} ---")
    config.print_config()


    # Set random seed if provided
    if seed is not None:
        random.seed(seed)
        # Note: numpy's random seed is not explicitly set here,
        # but 'random.seed()' can influence it indirectly in some cases.
        # For full reproducibility, you might consider np.random.seed(seed) as well if critical.

    # Initialize generators
    core_generator = CoreGenerator(config)
    component_generator = ComponentGenerator(config)
    task_generator = TaskGenerator(config)
    csv_writer = CSVWriter(config)

    # Generate cores
    cores = core_generator.generate_cores()

    # Distribute utilization among cores
    core_utils = core_generator.distribute_utilization(utilization / 100.0, cores)

    # Generate components
    components = component_generator.generate_components(cores, core_utils)

    # Distribute tasks among components
    tasks_per_component = task_generator.distribute_tasks(components)

    # Generate tasks (this will now potentially include sporadic tasks)
    tasks = task_generator.generate_tasks(components, tasks_per_component)

    # Adjust schedulability if needed
    tasks = component_generator.adjust_schedulability(components, tasks)

    # Write to CSV files
    csv_writer.write_csv_files(cores, components, tasks)

    print(f"Finished generating test case: {name}")



def main():
    """Generate a suite of test cases with different characteristics."""
    # Create output directory if it doesn't exist
    os.makedirs("Test_Cases", exist_ok=True)
    
    

    # In your generate_test_cases.py
    generate_test_case(
        name="definitely-unschedulable-high-task-load",
        num_cores=1,
        num_components=1, # Focus the overload on one component
        num_tasks=5,      # A few tasks are enough
        utilization=200,  # Force sum of task Ci/Ti to be very high
        schedulable=False,# This should ideally be handled by your generator's logic for unschedulable
        speed_range=(1.0, 1.0), # Keep core speed simple for clarity
        seed=789
    )

    generate_test_case(
        name="unschedulable-tight-core-budget-many-components",
        num_cores=1,
        num_components=3, # Multiple components competing
        num_tasks=9,      # Tasks distributed among components
        utilization=120,  # Overall system utilization is high
        schedulable=False,
        speed_range=(1.0, 1.0),
        seed=790
        # After generation, you might still want to manually check/tweak budgets.csv 
        # to ensure core budget (implicitly 1.0*CorePeriod) is less than sum of component demands
        # or that component budgets are too small for their assigned tasks.
    )


    # New Unschedulable Case Ideas:

    # 3. Unschedulable due to a very slow core
    generate_test_case(
        name="unschedulable-very-slow-core",
        num_cores=1,
        num_components=2,
        num_tasks=4,
        utilization=60, # Moderate utilization that *would* be schedulable on a normal core
        schedulable=False, # The speed factor should make it unschedulable
        speed_range=(0.1, 0.1), # Force a very slow core (10% speed)
        seed=101
    )
    # Why: Tests if WCETs are correctly scaled by speed_factor and if the
    #      analysis tool correctly identifies unschedulability due to insufficient processing capability.

    # 4. Unschedulable RM component due to one high-priority task starving others
    #    This requires careful task generation within a component.
    #    Set utilization for the component to be high, but schedulable if budgets were perfect.
    #    Then ensure one task has a very short period and moderate WCET.
    #    This might need temporary modification of task_generator.py for precise control
    #    or rely on the --unschedulable flag if it can create such internal component stress.
    generate_test_case(
        name="unschedulable-rm-priority-starvation",
        num_cores=1,
        num_components=1, # Focus on a single RM component
        num_tasks=3,      # e.g., 1 high-priority, 2 lower-priority
        utilization=80,   # High-ish for an RM component with 3 tasks (bound is ~0.779)
        schedulable=False,
        speed_range=(1.0, 1.0),
        seed=102
        # Note: After generation, inspect tasks.csv. If needed, manually adjust one task
        # in the RM component to have a very small period and a WCET that consumes
        # a large fraction of that period, to starve lower-priority tasks.
        # The component's scheduler should be RM. Modify budgets.csv if necessary.
    )
    # Why: Tests the RM schedulability analysis, especially the interference calculation.
    #      Your `analysis.py` `is_schedulable_rm_task` should identify this.

    # 5. Unschedulable due to Hierarchical Mismatch (Theorem 1 Violation - Delta)
    #    Parent BDR has a small delta, child BDR needs an even smaller or equal delta.
    #    This often requires manual tweaking of budgets.csv after generation if the
    #    generator doesn't directly control resulting BDR deltas.
    #    Alternatively, if your `find_minimal_bdr_interface` in `analysis.py` correctly
    #    derives deltas, you could aim to make a child component's tasks require a very responsive
    #    BDR (small delta), while the parent core (or parent component) inherently provides a larger delta.
    generate_test_case(
        name="unschedulable-bdr-delta-mismatch",
        num_cores=1,        # Parent is the core
        num_components=1,   # Child component
        num_tasks=3,        # Tasks that make the child component need a small delta
        utilization=70,
        schedulable=False, # The goal is that the *analysis* finds this unschedulable due to BDR rules
        speed_range=(1.0, 1.0),
        seed=103
        # How to encourage this:
        # - Give the child component tasks with short periods/deadlines.
        # - The analysis tool should derive a small delta for this child.
        # - If the core itself (parent_bdr) is considered to have delta=0 (ideal),
        #   and the child derives delta_C > 0, it should be fine.
        # - The tricky part is forcing the child's *required* delta to be problematic
        #   relative to a *non-zero* parent delta, or forcing the parent to have a larger delta
        #   than the child needs.
        # This specific scenario is harder to guarantee with generic generator flags and
        # might be better constructed by:
        #   a) Generating a base case.
        #   b) Running your analysis tool to see the derived (alpha, delta) for the component.
        #   c) Manually setting the parent core's (or a higher-level component's)
        #      effective BDR in your analysis logic to have a delta that violates Theorem 1
        #      (e.g., parent_delta >= child_delta, or child_delta_required < parent_delta_available).
        #      Or, manually edit budgets.csv for the *parent* if it were a component,
        #      giving it a (Q,P) pair that results in a large delta_parent.
    )
    # Why: Tests the hierarchical composition aspect (Theorem 1 in your `analysis.py`).
    #      Specifically, `child.delta > parent_bdr.delta` must hold.

    # 6. Unschedulable due to Hierarchical Mismatch (Theorem 1 Violation - Alpha)
    #    Sum of child BDR alphas exceeds parent BDR alpha.
    generate_test_case(
        name="unschedulable-bdr-alpha-sum-exceeded",
        num_cores=1,
        num_components=3, # Multiple children
        num_tasks=9,      # Enough tasks to give each component decent utilization
        utilization=90,   # High overall utilization for the core
        schedulable=False, # Target is unschedulable due to alpha sum
        speed_range=(1.0, 1.0),
        seed=104
        # How to encourage this:
        # - The generator assigns tasks to components.
        # - Your analysis tool calculates (alpha_C, delta_C) for each component.
        # - The sum of alpha_C for components on the core might naturally exceed the
        #   core's alpha (which is 1.0) if the total task load is high enough.
        # - If the parent is another component (not a core), its alpha_P could be < 1.0.
        #   Set `utilization` high enough that child components collectively demand more
        #   than the parent can supply.
    )
    # Why: Tests Theorem 1: sum of child alphas <= parent_alpha.

    # 7. Unschedulable due to a component that is internally schedulable by its tasks,
    #    but its derived BDR interface (alpha_C, delta_C) cannot be scheduled by the parent_bdr.
    #    This is a more subtle version of case 5 or 6.
    generate_test_case(
        name="unschedulable-valid-component-bad-parent-fit",
        num_cores=1,
        num_components=1,
        num_tasks=3,
        utilization=60, # Component itself might be fine
        schedulable=False, # But can't be scheduled by a constrained parent
        speed_range=(1.0, 1.0),
        seed=105
        # To achieve this:
        # 1. Generate the case.
        # 2. In your analysis tool or test script, when analyzing this component,
        #    manually define a `parent_bdr` for the core that has a very restrictive
        #    alpha (e.g., 0.2) or a delta that the component's derived delta cannot satisfy.
        #    For instance, if the component derives (alpha=0.5, delta=20),
        #    and you test it against parent_bdr = BDRModel(alpha=0.2, delta=5),
        #    it will fail on alpha. 
        #    If parent_bdr = BDRModel(alpha=0.6, delta=30), it will fail on delta (20 not > 30).
    )
    # Why: Tests the interaction between component-level BDR derivation and
    #      parent-level schedulability according to Theorem 1.

    # 8. Test case with sporadic tasks
    #    This is a more complex case, as it requires careful task generation.
    generate_test_case(
        name="small-unschedulable-sporadic-task-test-case",
        num_cores=1,
        num_components=1,
        num_tasks=5,
        utilization=50, # Moderate utilization
        schedulable=False, # This should be unschedulable
        speed_range=(1.0, 1.0),
        sporadic_ratio=0.3, # 30% sporadic tasks
        sporadic_deadline_range=(0.7, 1.0), # Deadline factor relative to MIT
        seed=106
    )

    # 9. Test case with sporadic tasks and a very high sporadic ratio
    generate_test_case(
        name="large-unschedulable-sporadic-task-test-case",
        num_cores=1,
        num_components=1,
        num_tasks=10,
        utilization=80, # Higher utilization
        schedulable=False, # This should be unschedulable
        speed_range=(1.0, 1.0),
        sporadic_ratio=0.8, # 80% sporadic tasks
        sporadic_deadline_range=(0.5, 1.0), # Deadline factor relative to MIT
        seed=107
    )

    # 10. schedulable case with sporadic tasks
    generate_test_case(
        name="small-schedulable-sporadic-task-test-case",
        num_cores=1,
        num_components=1,
        num_tasks=5,
        utilization=50, # Moderate utilization
        schedulable=True, # This should be schedulable
        speed_range=(1.0, 1.0),
        sporadic_ratio=0.3, # 30% sporadic tasks
        sporadic_deadline_range=(0.7, 1.0), # Deadline factor relative to MIT
        seed=108
    )

    print("\nAll test cases generated successfully!")


if __name__ == "__main__":
    main()