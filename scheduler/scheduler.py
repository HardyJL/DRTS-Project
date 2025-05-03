from models import Task, Component

def schedule_object(scheduler: str, object_list: list[Task] | list[Component]) -> list[Task] | list[Component]:
   """ Schedules the object_list given with the scheduling algorithm provided by the scheduler
   Args:
       scheduler (str): either RM or EDF which defines how to schedule
       object_list (list[Task] | list[Component]): list of components or tasks which will be scheduled
   Returns:
       list[Task] | list[Component]: the sorted list
   """
   assert scheduler == "EDF" or scheduler == "RM", "Incorrect Scheduler"
   if scheduler == "RM":
       return sorted(object_list, key= lambda obj: obj.priority)
   return sorted(object_list, key= lambda obj: obj.period)
