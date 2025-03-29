class Architecture: 
    def __init__(self, core_id, speed_factor,scheduler):
        self.core_id = core_id
        self.speed_factor = float(speed_factor)
        self.scheduler = scheduler

    def __repr__(self) -> str:
        return f"\nCore ID = ({self.core_id}) | Seed factor ({self.speed_factor}) | Scheduler ({self.scheduler})" 
