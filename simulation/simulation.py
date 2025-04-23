from models import Core

class Simulation:
    def simulate(self, core: list[Core]):
        print("Simulating...")
        # Set up a ready queue for each core this
        # Based on the algrithm of the core make sure to ready queu is the correct component
        # then for the component create a ready queue with the task
        for c in core:
            print(f"Core ID: {c}")
        pass
