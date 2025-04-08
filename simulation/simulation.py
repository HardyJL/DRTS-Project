from models import Core


class Simulation:
    def simulate(self, core: list[Core]):
        print("Simulating...")
        for c in core:
            print(f"Core ID: {c}")
        pass
