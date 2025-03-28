class Architecture: 
    def __init__(self, core_id, speed_factor):
        self.core_id = core_id
        self.speed_factor = float(speed_factor)

    def __repr__(self) -> str:
        return f"Core ID = ({self.core_id}) | Seed factor ({self.speed_factor})" 
