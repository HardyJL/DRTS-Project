import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from math import lcm, floor
from models import Core, Component, Task, Solution
#from scheduler import schedule_object





#---------functions from main to help make analysis work - delete when everything works!!----------------
from csv_functions import load_models_from_csv

def load_models(architectures, tasks, budgets):
    cores, tasks, components = load_models_from_csv(architectures, Core), load_models_from_csv(
        tasks, Task), load_models_from_csv(budgets, Component)

   # assert len(cores) > 0 and len(tasks) > 0 and len(
    #    components) > 0, "No cores, tasks or components found in the csv files"

    for component in components:
        component.tasks = [
            task for task in tasks if task.component_id == component.component_id]

    for core in cores:
        core.components = [
            component for component in components if component.core_id == core.core_id]

    return cores







def analysis():

    #assert len(sys.argv) == 3 and sys.argv[1] != "" and sys.argv[1] != None
    # check if the expected path is correct
    expected_path = r"C:\Users\Laurits\Documents\masters_degree\2nd_semester\Distributed_real_time_systems\DRTS_Project-Test-Cases\3-medium-test-case"
    assert os.path.exists(
        expected_path), f"Path {expected_path} does not exist"

    architectures, tasks, budgets = expected_path + \
        "/architecture.csv", expected_path + "/tasks.csv", expected_path + "/budgets.csv"
    assert os.path.exists(architectures) and os.path.exists(tasks) and os.path.exists(
        budgets), f"Path {architectures} or {tasks} or {budgets} does not exist"

    cores = load_models(architectures, tasks, budgets)












    # --------------- Math---------------------
# worst case execution time for task
    def C(task_index, task_list):
        return int(task_list[task_index].wcet)

    # period of task
    def T(task_index, task_list):
        return int(task_list[task_index].period)

    # deadline of task (deadline = period unless explicitly stated)
    def D(task_index, task_list):
        return int(task_list[task_index].period)

    # demand bound function (dbf) for EDF with implicit deadline (equation 2)
    def dbf_EDF_implicit(t, task_list):
        cumulative_resources = 0
        for i in range(len(task_list)):
            cumulative_resources += floor(t / T(i, task_list)) * C(i, task_list)
        return cumulative_resources

    # demand bound function (dbf) for EDF with explicit deadline (equation 3)
    def dbf_EDF_explicit(t, task_list):
        cumulative_resources = 0
        for i in range(len(task_list)):
            cumulative_resources += floor((t + T(i, task_list) - D(i, task_list)) / T(i, task_list)) * C(i, task_list)
        return cumulative_resources

    # demand bound function (dbf) for RM with implicit deadline   (equation 4)
    def dbf_RM_implicit(t, given_task_index, task_list):
        cumulative_resources = C(given_task_index, task_list)
        for k in range(len(task_list)):
            if task_list[given_task_index].priority < task_list[k].priority:
                cumulative_resources += floor(t / T(k, task_list)) * C(k, task_list)
        return cumulative_resources




# ---------------- BDR model---------------------------------------------

    def get_budget(input_core_id):
        budget_entries = []
        for core in cores:
            for component in core.components:
                if component.core_id == input_core_id:
                    budget_entries.append((component.component_id, component.budget))
        return budget_entries  
    
    def get_periods(input):
        component_periods = []
        for i in cores:
            for j in i.components:
                if j.core_id == input:
                    component_periods.append(j.period)
        return component_periods
        
    


    def calculate_component_srp(input_core_id):
        """Calculates the SRP model (Gamma, P) for each component on a given core."""

        core_budgets = []
        core_budgets = get_budget(input_core_id)

        
        component_periods = []
        component_periods = get_periods(input_core_id)
       


        partition_period = lcm(*map(int, component_periods))
        
        print("partion_period")
        print(partition_period)


        #Sort by budget amount to allocate correct
        core_budgets_sorted = sorted(core_budgets, key=lambda x: x[1])  
        print("core budgets sorted")
        print(core_budgets_sorted)

        # 2. Allocate time proportional to budget - TDMA approach
        gamma = {}
        current_time = 0

        for component_id, budget in core_budgets_sorted:
            component_start = current_time
            component_end = component_start + budget
            gamma[component_id] = (component_start, component_end)
            current_time = component_end

        return gamma, partition_period


    
    #gamma1, partion1 = calculate_component_srp("Core_1")
    #print(f"gamma: {gamma1}")
    #print(f"partion_period: {partion1}")
    
    def calculate_availability_factor(srp_gamma: list, srp_period: int):
        """Calculates the availability factor (alpha) for a given SRP model."""
        total_available_time = 0
        for key, value in srp_gamma.items():
            total_available_time += value[1]-value[0]
        alpha = total_available_time / srp_period
        return alpha
    
    def calculate_availability_factor1(srp_gamma: list, srp_period: int):
        """Calculates the availability factor (alpha) for a given SRP model."""
        total_available_time = 0
        for interval in srp_gamma:
        # Remove the brackets and split by comma
            clean = interval.strip("[]()")
            start_str, end_str = clean.split(",")
            start = float(start_str.strip())
            end = float(end_str.strip())
            total_available_time += end - start
        return total_available_time / srp_period

    
    def partition_delay(srp_gamma: list, srp_period: int):
        """estimate of partition delay - so far assume it's 0. the 
        the partition delay equals δ for any t0 to t where: (t0 ≥ 0,t ≥ 0), (t - δ) x α(R) ≤ sft0 (R,t) ≤ (t +δ)x α(R). """
        return 0
    


    def analyze_bdr_model(input_cores):
        """Analyzes the BDR model for each core."""

        for core in input_cores:
            print(f"\nBDR Analysis for Core: {core.core_id}")

            srp_gamma, srp_period = calculate_component_srp(core.core_id)

            print(f"  SRP Gamma: {srp_gamma}")
            print(f"  SRP Period: {srp_period}")

            alpha = calculate_availability_factor(srp_gamma, srp_period)
            # The next line will now return 0 as it is not used
            delta = partition_delay(srp_gamma, srp_period)

            print(f"  Availability Factor (alpha): {alpha}")
            print(f"  Partition Delay (delta): {delta}")
            srp_string_values = ""
            #Print the value of all the SRP's
            if (len(srp_gamma) != 0):
                print("The values for each of the SPR's:")
                for key, value in srp_gamma.items():
                    srp_string_values += key +":"+str(value)+","
                print(srp_string_values[:-1])

    # Get tasks local to each component
            for component in core.components:
                component_tasks = component.tasks
                print(f"\n  Component: {component.component_id}, Scheduler: {core.scheduler}")

                # EDF Schedulability Test
                if core.scheduler == "EDF":
                    if component_tasks:
                        is_schedulable = True
                        for t in range(1, srp_period + 1):  # Test up to the period
                            demand = dbf_EDF_implicit(t, component_tasks)
                            if demand > alpha * t:
                                is_schedulable = False
                                break
                        print(f"    EDF Schedulability: {'YES' if is_schedulable else 'NO'}")
                    else:
                        print("    No tasks for this component.")

                # RM Schedulability Test
                elif core.scheduler == "RM":
                    if component_tasks:
                         is_schedulable = True
                         for i in range(len(component_tasks)):
                            response_time = dbf_RM_implicit(T(i,component_tasks),i,component_tasks)
                            
                            if response_time > T(i,component_tasks):
                                is_schedulable = False

                                break
                                
                         print(f"    RM Schedulability: {'YES' if is_schedulable else 'NO'}")
                    else:
                        print("    No tasks for this component.")




    analyze_bdr_model(cores)



    #extra thing for visualisation
    #print(f"Number of tasks: {len(all_tasks)}")
    #for i, t in enumerate(all_tasks):
    #    print(f"Task {i}: wcet={t.wcet}, period={t.period}")

    #print(dbf_EDF_implicit(20))




# ----------TODO-----------
"""     * find out how to calculate partition delay 
        * implement theorem 1 and 2
        * clean up code and make sure that the input for analysis is the same as for simulation"""






# Run the analysis function
if __name__ == "__main__":
    analysis()
