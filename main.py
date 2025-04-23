from models import Task
import sys
import os.path
from Simulation.simulation import simulation

"""
To run:
python3 main.py <test> <cycles>

python3 main.py 1-tiny-test-case 100
python3 main.py 2-small-test-case 100


"""

if __name__ == "__main__":





    #Check input is right size
    if len(sys.argv) < 3:
        print("Too few arguments")
        sys.exit(-1)

    elif len(sys.argv)> 3:
        print("Too many arguments")
        sys.exit(-1)


    #Check if folders exist
    if not os.path.exists(os.path.join(os.getcwd(), "Test_Cases/"+sys.argv[1])):
        print("Test folder doesnt exist")
        sys.exit()
    #ensure cycles is int
    try:
        max_cycles=int(sys.argv[2])
    except:
        print("max cycles must be an intreger")

    
    #task = Task(task_id= "Test", wcet=1, deadline=1, core_assignment="core1")
    #print(task)
    ######################START SIMULATION#####################
    simulation(os.path.join(os.getcwd(),"Test_Cases/",sys.argv[1]), max_cycles)
