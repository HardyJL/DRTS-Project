import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from math import lcm, floor
from models import Core, Component, Task, Solution
#from scheduler import schedule_object





#---------functions from main to help make analysis work - delete when everything works!!----------------
from csv_functions import load_models_from_csv

def load_models(architectures, tasks, budgets, solutions_path):
    cores = load_models_from_csv(architectures, Core)
    tasks = load_models_from_csv(tasks, Task)
    components = load_models_from_csv(budgets, Component)
    solutions = load_models_from_csv(solutions_path, Solution)

    for component in components:
        component.tasks = [
            task for task in tasks if task.component_id == component.component_id]

    for core in cores:
        core.components = [
            component for component in components if component.core_id == core.core_id]
        
        # 💡 Assign solutions to core
        #core.solutions = [
        #    solution for solution in solutions if solution.component_id == component.component_id]

    return cores, solutions




def analysis():

    assert len(sys.argv) == 2 and sys.argv[1] != "" and sys.argv[1] != None
    expected_path = os.path.join(os.getcwd(), sys.argv[1])
    # check if the expected path is correct
    # expected_path = r"/mnt/D/Egyetem/MSem2_2025/Dist_RTS/DRTS-Project/Test-Cases/4-large-test-case"
    assert os.path.exists(
        expected_path), f"Path {expected_path} does not exist"

    architectures, tasks, budgets, solutions = expected_path + \
        "/architecture.csv", expected_path + "/tasks.csv", expected_path + "/budgets.csv",  expected_path + "/_solutions.csv"
    assert os.path.exists(architectures) and os.path.exists(tasks) and os.path.exists(
        budgets), f"Path {architectures} or {tasks} or {budgets} does not exist"

    cores, solutions1 = load_models(architectures, tasks, budgets, solutions)












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

    def get_budget_component(input_core_id):
        budget_entries = []
        for core in cores:
            for component in core.components:
                if component.core_id == input_core_id:
                    budget_entries.append((component.component_id, component.budget))
        return budget_entries  
    
    def get_budget_task(input_component_id):
        """getter for budget for task - the output is the budget from the component of the relating task becasue tasks dont contain budget"""
        budget_task =  0
        for i in cores:
            for j in i.components:
                if j.component_id == input_component_id:
                    budget_task = j.budget
        return budget_task


    def get_periods_component(input):
        component_periods = []
        for i in cores:
            for j in i.components:
                if j.core_id == input:
                    component_periods.append(j.period)
        return component_periods
        
    def get_periods_tasks(input):
        """input: the component of the tasks"""
        task_periods = []
        for i in cores:
            for j in i.components:
                if j.component_id == input:
                    for task in j.tasks:
                        task_periods.append(task.period)
        return task_periods
    
    
    def calculate_task_srp1(input_component_id, input_core):
        """calculates the srp model (Gamma, P) for each task on a given component"""
        taskList = []
        for core in cores:
            for component in core.components:
                if component.component_id == input_component_id:
                    taskList = component.tasks
        
        
        
        maxTasks =  len(taskList)   #Max length will then be total times

        totalAccess = 0 #The time you will have access. If so it has to be
        partition_period = 0  #Get's time to know
        for task in taskList:  #For access to every access
            srp_gamma_component, srp_period_component = calculate_component_srp(input_core) #Calcualte the component

        
        totalAccess += srp_period_component

        partition_period += totalAccess #Get the ammount of access for tasks

        gamma = []

        currentTime = 0

        testValue = 0
        checkPoint =0 #If the current time doesn't meet requirements then
        for i in range(0,maxTasks):

            print("Loop test")
            testValue += 10
            if checkPoint > (partition_period):
                break
            if (True):#Get a function that will be that you can access those SRP
                component_start = currentTime
                component_end = testValue
                gamma.append((component_start, component_end)) #Append the results
                currentTime = component_end#Change the time
                checkPoint += i #Check value now

        return gamma, partition_period

    def calculate_task_srp(component_id_input):
        """calculates the srp model (Gamma, P) for each task on a given component"""

        component_budget = 0
        component_budget = get_budget_task(component_id_input)

        task_periods = []
        task_periods = get_periods_tasks(component_id_input)

        partition_period = lcm(*map(int, task_periods))

        task_periods_sorted = sorted(task_periods)  
        
        
        gamma = {}
        current_time = 0




        for task_id in task_periods_sorted:
            component_start = current_time                           #delete this out maybe and use result from simulator instead
            component_end = component_start + component_budget
            gamma[task_id] = (component_start, component_end)
            current_time = component_end

        return gamma, partition_period


    def calculate_component_srp(core_id_input):
        """Calculates the SRP model (Gamma, P) for each component on a given core."""

        

        core_budgets = []
        core_budgets = get_budget_component(core_id_input)

        
        component_periods = []
        component_periods = get_periods_component(core_id_input)
       


        partition_period = lcm(*map(int, component_periods))
        
        #print("partion_period")
        #print(partition_period)
        

        #Sort by budget amount to allocate correct
        core_budgets_sorted = sorted(core_budgets, key=lambda x: x[1])  
        #print("core budgets sorted")
        #print(core_budgets_sorted)

        # 2. Allocate time proportional to budget - TDMA approach
        gamma = {}
        current_time = 0

        for component_id, budget in core_budgets_sorted:
            component_start = current_time                           #delete this out maybe and use result from simulator instead
            component_end = component_start + budget
            gamma[component_id] = (component_start, component_end)
            current_time = component_end

        return gamma, partition_period
    

    
    def calculate_availability_factor(srp_gamma, srp_period: int):
        """Calculates the availability factor (alpha) for a given SRP model."""
        total_available_time = 0
        # print(srp_gamma)
        """Handle tuples with different formats"""
        try:
            for key, value in srp_gamma.items():
                total_available_time += value[1]-value[0]
        except AttributeError:
            for value in srp_gamma:
                total_available_time += value[1]-value[0]
        alpha = total_available_time / srp_period
        
        return alpha
    
    def calculate_availability_factor2(srp_gamma, srp_period: int):
        """Calculates the availability factor (alpha) for a given SRP model."""
        total_available_time = 0
        for interval in srp_gamma:  # srp_gamma is a list of (start, end)
            total_available_time += interval[1] - interval[0]
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

    # use solution ordering for this
    
    #for i in solutions1:
    #    print(i)

         
    def partition_delay(srp_gamma, srp_period, input_core, input_component):
        """Estimates the partition delay based on the solutions dataset and SRP parameters."""

        alpha = calculate_availability_factor(srp_gamma,srp_period)
        
        #Get values from the srp gamma
        # print("***Debug***")
        # print(srp_gamma)

        """Handle tuples with different formats"""
        try:
            gamma_values = list(srp_gamma.values())
        except AttributeError:
            gamma_values = srp_gamma

        #Worst case is the worst WCET of task times 2
        gammaValue = max( [y-x for x, y in gamma_values]) #Maximum of 2 for best to 5

        #We assume the amount of time it needs to reach
        amountOfTime = []
        for core in input_core:
            for solu in solutions1:

                if solu.component_id == input_component:
                    amountOfTime = [solu.avg_response_time]

        #Calculate the delays
        delay = (alpha*srp_period)/ amountOfTime[0]

        # If there are no tasks, delay is 0
        if (len(tasks) == 0):
            delay = 0
        #print(amountOfTime[0])

        #If it overbounds
        if (alpha*srp_period) <= gammaValue:
            delay = 0
        # if (len(tasks) != 0): #If not empty
            
        #     return delay
        #print("component")
        return delay #No tasks = 0 delay

    #def theorem1(rescource_partition_group):

    


    def analyze_bdr_model(input_cores):
        """Analyzes the BDR model for each core."""

        for core in input_cores:
            

            srp_gamma_component, srp_period_component = calculate_component_srp(core.core_id)

            

            alpha_component = calculate_availability_factor(srp_gamma_component, srp_period_component)
            # The next line will now return 0 as it is not used
            #delta = partition_delay(srp_gamma, srp_period)




            # Get tasks local to each component
            for component in core.components:
                component_tasks = component.tasks


                

                print(f"\nBDR Analysis for Core: {core.core_id}")
                print(f"  SRP Gamma: {srp_gamma_component}")
                print(f"  SRP Period: {srp_period_component}")
                print(f"  ----- Availability Factor (alpha): {alpha_component}")
                #print(f"  Partition Delay (delta): {delta}")
                srp_string_values = ""
                #Print the value of all the SRP's
                if (len(srp_gamma_component) != 0):
                    print("The values for each of the SPR's:")
                    for key, value in srp_gamma_component.items():
                        srp_string_values += key +":"+str(value)+","
                    print(srp_string_values[:-1])


                


                print(f"\n  Component: {component.component_id}, Scheduler: {core.scheduler}")


                
                # the delay for the component(the parent partition)
                delay_component = partition_delay(srp_gamma_component, srp_period_component, input_cores, component.component_id)
                print(f"---- this is the partition delay {delay_component}")


                


               
                


                # THIS PART IS COMMENTED OUT BUT THIS PART IS THE ONE THAT SHOULD WORK - IVE JUST NOT FINISHED THE DEBUGGING OF IT..   THE OTHER VERSION DOWN BELOW KINDA WORKS BUT IS INCORRECT

                #rescource partition group (rpg)
                rpg = []
                
                alpha = []
                delay = []
                srp_gamma_tasks, srp_period_tasks= calculate_task_srp1(component.component_id, core)
                
                for task in srp_gamma_tasks:
                    #calculate srp, availability factor and partition delay for task (child)
                    #srp_gamma_task, srp_period_task= calculate_task_srp(component.component_id)
                    alpha_task = calculate_availability_factor2(srp_gamma_tasks, srp_period_tasks)
                    delay_task = partition_delay(srp_gamma_tasks, srp_period_tasks, input_cores, component.component_id)

                    rpg.append((task, alpha_task, delay_task))
                


                    
                    alpha.append(alpha_task)
                    delay.append(delay_task)

                
                gamma1, alpha1, delay1 = rpg[1]
                print(f"this is gamma-child {gamma1}\n this is alpha-child {alpha1}\n this is delay-child {delay1}")
                
                #schedulability test by therorem 1:
                

                gamma1, alpha1, delay1 = rpg[1]

                sum_alpha = sum(alpha)
                sum_delay = sum(delay)

                if len(rpg) > 0 : #To check if a component
                    
                    if (sum_alpha < alpha_component) : #If the results are all true
                        is_Schedulable = False #Default is false and check that for test

                        for result in delay: #Iteratre and run through 
                            if  result > delay_component: #If they all meet this constraint we can sched
                                is_Schedulable = True #Set to say that all the conditions are good.

                        if is_Schedulable: #State if good or not
                            print("Scheduability from theorem 1: YES!")
                        else:
                            print("Scheduability from theorem 1: NO!")
                    else:
                        print("Scheduability from theorem 1: NO!")









                # WHEN THE ABOVE VERSION WORKS, COMMENT/DELETE THIS VERSION.

                #rescource partition group (rpg)
                """
                rpg = []
                
                alpha = []
                delay = []
                
                
                for task in component.tasks:
                    #calculate srp, availability factor and partition delay for task (child)
                    srp_gamma_task, srp_period_task= calculate_task_srp(component.component_id)
                    alpha_task = calculate_availability_factor(srp_gamma_task, srp_period_task)
                    delay_task = partition_delay(srp_gamma_task, srp_period_task, input_cores, component.component_id)

                    rpg.append((srp_gamma_task, alpha_task, delay_task))
                


                    
                    alpha.append(alpha_task)
                    delay.append(delay_task)

                
                gamma1, alpha1, delay1 = rpg[1]
                print(f"this is gamma-child {gamma1}\n this is alpha-child {alpha1}\n this is delay-child {delay1}")
                
                #schedulability test by therorem 1:
                

                gamma1, alpha1, delay1 = rpg[1]

                sum_alpha = sum(alpha)
                sum_delay = sum(delay)

                if len(rpg) > 0 : #To check if a component
                    
                    if (sum_alpha < alpha_component) : #If the results are all true
                        is_Schedulable = False #Default is false and check that for test

                        for result in delay: #Iteratre and run through 
                            if  result > delay_component: #If they all meet this constraint we can sched
                                is_Schedulable = True #Set to say that all the conditions are good.

                        if is_Schedulable: #State if good or not
                            print("Scheduability from theorem 1: YES!")
                        else:
                            print("Scheduability from theorem 1: NO!")
                    else:
                        print("Scheduability from theorem 1: NO!")"""
                        









    analyze_bdr_model(cores)
    

    #extra thing for visualisation
    #print(f"Number of tasks: {len(all_tasks)}")
    #for i, t in enumerate(all_tasks):
    #    print(f"Task {i}: wcet={t.wcet}, period={t.period}")

    #print(dbf_EDF_implicit(20))




# ----------TODO-----------
"""     * change calculate srp so that it can do it for both components and tasks - right now it can only do components then do the same for partition-delay
        * implement theorem 1 and 2
        * clean up code and make sure that the input for analysis is the same as for simulation"""






# Run the analysis function
if __name__ == "__main__":
    analysis()
