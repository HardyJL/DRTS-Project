from models.core import Core
from models.component import Component
from models.solution import Solution
from models.task import Task
from models.job import Job
import csvs.csv_functions
import os.path
from scheduler import Scheduler



# Assume models (Core, Component, Task, Job) and csv_functions are defined

def simulation(test_folder: str, max_simulation_time: float):
    print("Starting the simulation...\n--------------------------------------------------")
    # --- Load data, create dicts, assign tasks/components ---
    cores, components_list, tasks_list = csvs.csv_functions.load_models_from_csv(test_folder)
    cores_dict: dict[str, Core] = {core.core_id: core for core in cores}
    components_dict: dict[str, Component] = {comp.component_id: comp for comp in components_list}
    # (Assignment logic...)
    for comp_id, comp_obj in components_dict.items():
        if comp_obj.core_id in cores_dict: cores_dict[comp_obj.core_id].assign_component(comp_obj)
    for task_obj in tasks_list:
        if task_obj.component_ID in components_dict: components_dict[task_obj.component_ID].assign_task(task_obj)


    # --- Initialize Simulation State ---
    current_time = 0.0
    completed_jobs_log = {task.task_name: [] for task in tasks_list}
    epsilon = 1e-9 # Tolerance for float comparisons

    # --- Initialize Next Event Times and Component State ---
    task_next_arrival_time: dict[str, float] = {}
    comp_next_replenish_time: dict[str, float] = {}

    print("Initializing state and first events...")
    for comp_id, component in components_dict.items():
        component.current_budget = component.budget
        component.ready_queue = []
        component.running_job = None
        if component.period > 0:
            comp_next_replenish_time[comp_id] = component.period
            print(f"  Comp {comp_id}: Initial budget {component.budget:.2f}, next replenish at {component.period:.2f}")
        else:
             comp_next_replenish_time[comp_id] = float('inf') # Never replenishes if period is 0

        core_id = component.core_id
        core_speed = cores_dict[core_id].speed_factor if core_id in cores_dict else 1.0
        for task_name, task in component.tasks.items():
            task_next_arrival_time[task_name] = 0.0 # Assume synchronous start
            # Create and add the first job
            first_job = Job(task_ref=task, arrival_time=0.0, core_speed_factor=core_speed)
            component.add_job_to_ready_queue(first_job)
            print(f"  Task {task_name}: First arrival at 0.0, Job {first_job.job_id} created.")

    for core in cores_dict.values():
        core.running_component_id = None # Ensure cores start idle


    scheduler = Scheduler() # Instantiate your scheduler helper
    last_progress_time = -1 # For detecting potential stalls

    # --- Main Simulation Loop ---
    while current_time <= max_simulation_time:

        # --- 1. Calculate Next Potential Event Times ---
        min_arrival = min(task_next_arrival_time.values()) if task_next_arrival_time else float('inf')
        min_replenish = min(comp_next_replenish_time.values()) if comp_next_replenish_time else float('inf')

        min_potential_completion = float('inf')
        potential_completion_sources = [] # Store (time, core_id, comp_id, job_id)
        for core_id, core in cores_dict.items():
            comp_id = core.running_component_id
            if comp_id and comp_id in components_dict:
                component = components_dict[comp_id]
                job = component.running_job
                if job and job.state == "RUNNING":
                    # Check if budget or wcet is the limit
                    time_to_finish_wcet = job.remaining_wcet
                    time_to_finish_budget = component.current_budget

                    # Can only run for min of the two
                    time_can_run = min(time_to_finish_wcet, time_to_finish_budget)

                    if time_can_run < epsilon: # Effectively cannot run
                         potential_comp_time = float('inf')
                    else:
                         potential_comp_time = current_time + time_can_run
                    
                    min_potential_completion = min(min_potential_completion, potential_comp_time)
                    potential_completion_sources.append( (potential_comp_time, core_id, comp_id, job.job_id))


        # --- 2. Determine Next Simulation Time and Time Delta ---
        next_time = min(min_arrival, min_replenish, min_potential_completion)

        if next_time == float('inf'):
             print("No more events possible. Exiting.")
             break # No future events

        if next_time < current_time - epsilon:
             print(f"Warning: Time moving backwards? next_time={next_time}, current_time={current_time}. Skipping step.")
             # This indicates a potential logic error, maybe skip or break
             break 

        time_delta = max(0, next_time - current_time) # Ensure non-negative delta

        print(f"\n--- Time {current_time:.2f} -> {next_time:.2f} (Delta: {time_delta:.2f}) ---")
        print(f"    Next Times: Arrival={min_arrival:.2f}, Replenish={min_replenish:.2f}, Completion={min_potential_completion:.2f}")

        # Safety break for potential infinite loops if time doesn't advance
        if time_delta < epsilon and current_time == last_progress_time:
             print("Warning: Simulation time not advancing. Potential infinite loop or immediate events. Breaking.")
             # You might need more sophisticated handling here if immediate events are valid
             break
        if time_delta > epsilon:
            last_progress_time = current_time # Record time only when it advances significantly


        # --- 3. Update Progress of Running Jobs ---
        jobs_completing_now = []
        for core_id, core in cores_dict.items():
            comp_id = core.running_component_id
            if comp_id and comp_id in components_dict:
                component = components_dict[comp_id]
                job = component.running_job
                if job and job.state == "RUNNING":
                    run_amount = min(time_delta, component.current_budget)
                    if run_amount > epsilon:
                         print(f"  Core {core_id}: Job {job.job_id} ran for {run_amount:.2f}.")
                         job.remaining_wcet -= run_amount
                         component.current_budget -= run_amount
                         print(f"    Job {job.job_id} rem_wcet: {job.remaining_wcet:.2f}, Comp {comp_id} rem_budget: {component.current_budget:.2f}")

                         # Check for completion due to this run_amount
                         if job.remaining_wcet < epsilon:
                             jobs_completing_now.append((core_id, comp_id, job))
                             print(f"    >> Job {job.job_id} will complete at {next_time:.2f}")
                         # Check for budget exhaustion
                         if component.current_budget < epsilon:
                              print(f"    >> Comp {comp_id} exhausted budget during interval.")
                              job.state = "READY" # Paused due to budget


        # --- 4. Advance Clock ---
        current_time = next_time

        # --- 5. Process Events Occurring Exactly at current_time ---
        processed_event = False

        # -- Check Arrivals --
        arriving_tasks = [name for name, time in task_next_arrival_time.items() if abs(time - current_time) < epsilon]
        if arriving_tasks:
            processed_event = True
            print(f"  Event(s) at {current_time:.2f}: JOB_ARRIVAL")
            for task_name in arriving_tasks:
                task = None
                # Find the task object (this is inefficient, consider passing task obj)
                for t in tasks_list:
                    if t.task_name == task_name:
                        task = t
                        break
                if task:
                    component = components_dict[task.component_ID]
                    core_speed = cores_dict[component.core_id].speed_factor
                    new_job = Job(task_ref=task, arrival_time=current_time, core_speed_factor=core_speed)
                    component.add_job_to_ready_queue(new_job)
                    print(f"    Job {new_job.job_id} arrived for Comp {component.component_id}")
                    # Update next arrival time for this task
                    task_next_arrival_time[task_name] += task.period
                else:
                    print(f"    Error: Task {task_name} not found during arrival event.")


        # -- Check Replenishments --
        replenishing_comps = [cid for cid, time in comp_next_replenish_time.items() if abs(time - current_time) < epsilon]
        if replenishing_comps:
            processed_event = True
            print(f"  Event(s) at {current_time:.2f}: BUDGET_REPLENISH")
            for comp_id in replenishing_comps:
                component = components_dict[comp_id]
                component.current_budget = component.budget
                print(f"    Comp {comp_id} replenished budget to {component.budget:.2f}")
                # Update next replenish time for this component
                comp_next_replenish_time[comp_id] += component.period

        # -- Process Completions --
        if jobs_completing_now:
            processed_event = True
            print(f"  Event(s) at {current_time:.2f}: JOB_COMPLETION")
            for core_id_comp, comp_id_comp, job_comp in jobs_completing_now:
                print(f"    Job {job_comp.job_id} COMPLETED.")
                job_comp.state = "COMPLETED"
                job_comp.completion_time = current_time
                job_comp.response_time = current_time - job_comp.arrival_time
                completed_jobs_log[job_comp.task_ref.task_name].append(job_comp.response_time)

                # Clear from component and core
                if components_dict[comp_id_comp].running_job == job_comp:
                    components_dict[comp_id_comp].running_job = None
                # Core will become idle unless rescheduled below


        if not processed_event and time_delta > epsilon :
             print(f"  Event at {current_time:.2f}: Potential Completion Time Reached (no other events)")
             # This means min_potential_completion was the trigger. One or more jobs might have
             # finished exactly now OR run out of budget exactly now. This is handled
             # implicitly by the completion/budget checks in step 3 and 5.


        # --- 6. Make Scheduling Decisions ---
        print("  Making Scheduling Decisions...")
        for core_id, core in cores_dict.items():
             print(f"    Core {core_id}:")
             # (Identical Scheduling Logic as in the previous event-queue example)
             # Select highest priority eligible component (using core.scheduler - PLACEHOLDER)
             # --- Core-Level Scheduling: Select Component ---
             eligible_components = core.get_eligible_components() # Components with budget & work
             highest_priority_component: Component | None = None
             if not eligible_components:
                 print(f"      No eligible components.")
                 if core.running_component_id:
                      print(f"      Stopping component {core.running_component_id}")
                      if core.running_component_id in components_dict:
                           old_comp = components_dict[core.running_component_id]
                           if old_comp.running_job and old_comp.running_job.state == "RUNNING":
                               old_comp.running_job.state = "READY"
                      core.running_component_id = None
             else:
                  # TODO: Implement proper core-level EDF/RM component selection here!
                  highest_priority_component = eligible_components[0] # Placeholder!
                  print(f"      Eligible components: {[c.component_id for c in eligible_components]}. Chosen (placeholder): {highest_priority_component.component_id}")
                  if core.running_component_id != highest_priority_component.component_id:
                      print(f"      Core Preemption: Comp '{core.running_component_id}' -> Comp '{highest_priority_component.component_id}'")
                      if core.running_component_id and core.running_component_id in components_dict:
                           old_comp = components_dict[core.running_component_id]
                           if old_comp.running_job and old_comp.running_job.state == "RUNNING":
                               old_comp.running_job.state = "READY"
                      core.running_component_id = highest_priority_component.component_id
                  else:
                      print(f"      Component {core.running_component_id} continues potentially.")

             # Select highest priority job within the chosen component (using component.scheduler)
             # --- Component-Level Scheduling: Select Job ---
             if core.running_component_id and core.running_component_id in components_dict:
                 current_component = components_dict[core.running_component_id]
                 current_job = current_component.running_job
                 next_job_to_run = current_component.get_next_job_to_run() # Sorts readyQ and returns [0]

                 if not next_job_to_run:
                      print(f"      Component {current_component.component_id}: No ready jobs.")
                      # If a job was running, it must have just completed. Mark component idle.
                      if current_job:
                           current_component.running_job = None # Ensure it's cleared
                 elif current_job != next_job_to_run:
                      print(f"      Comp {current_component.component_id} Preemption/Switch: Job '{current_job.job_id if current_job else 'None'}' -> Job '{next_job_to_run.job_id}'")
                      if current_job and current_job.state == "RUNNING":
                          current_job.state = "READY" # Mark preempted job as ready
                          # It should still be in component.running_job until replaced

                      current_component.running_job = next_job_to_run
                      next_job_to_run.state = "RUNNING"
                      if next_job_to_run.start_time is None: next_job_to_run.start_time = current_time
                      current_component.remove_job_from_ready_queue(next_job_to_run) # Remove *after* selection
                 elif current_job == next_job_to_run:
                      # Job continues or resumes (if paused for budget)
                      if current_job.state != "RUNNING":
                           print(f"      Component {current_component.component_id}: Job {current_job.job_id} resumes.")
                           current_job.state = "RUNNING" # Ensure it's marked running
                      else:
                            print(f"      Component {current_component.component_id}: Job {current_job.job_id} continues.")
                 else: # Should not happen if next_job_to_run exists but current_job is different
                      print(f"      Component {current_component.component_id}: Logical error in scheduling.")

        # --- Loop End ---


    # --- Simulation End ---
    print(f"\n--- Simulation Finished at time {current_time:.2f} ---")
    # --- Calculate and Report Results (as before) ---
    # ...