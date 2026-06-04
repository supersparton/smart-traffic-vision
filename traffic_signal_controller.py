import time

# PCU (Passenger Car Unit) weights based on Indian road conditions
# These represent how much "space" and "clearance time" each vehicle takes relative to a car.
VEHICLE_WEIGHTS = {
    "car": 1.0,
    "Rikshaw": 0.8,
    "motorbike": 0.4,
    "bus": 3.0,
    "truck": 3.5
}

class TrafficSignalController:
    """
    Manages the adaptive signal cycle for a 4-way intersection.
    Phases: 0:North, 1:East, 2:South, 3:West
    """
    def __init__(self):
        self.phases = ["North", "East", "South", "West"]
        self.current_phase_index = 0
        self.state = "GREEN"  # GREEN, YELLOW, ALL_RED
        
        self.min_green = 10
        self.max_green = 60
        self.yellow_duration = 3
        self.all_red_duration = 2
        self.time_per_pcu = 2.0  # seconds per PCU count
        
        # Current timer for the active state
        self.timer = 0
        self.last_update_time = time.time()
        
        # State storage for all lanes
        self.lane_data = {
            lane: {"count": 0, "pcu": 0, "green_time": 15} 
            for lane in self.phases
        }
        self.timer = self.lane_data[self.phases[0]]["green_time"]

    def calculate_pcu(self, vehicle_counts):
        """
        vehicle_counts: dict like {"car": 2, "bus": 1, ...}
        """
        total_pcu = 0
        for vtype, count in vehicle_counts.items():
            total_pcu += VEHICLE_WEIGHTS.get(vtype, 1.0) * count
        return total_pcu

    def get_green_time(self, pcu):
        """Calculates green time based on pcu density."""
        calculated = pcu * self.time_per_pcu
        return max(self.min_green, min(self.max_green, calculated))

    def update_lane_data(self, lane_name, vehicle_counts):
        """Updates density data with weighted smoothing to prevent jumps."""
        new_pcu = self.calculate_pcu(vehicle_counts)
        new_count = sum(vehicle_counts.values())
        
        # Weighted Smoothing (80% old, 20% new)
        old_data = self.lane_data[lane_name]
        pcu = (old_data["pcu"] * 0.8) + (new_pcu * 0.2)
        count = round((old_data["count"] * 0.8) + (new_count * 0.2))
        
        green_time = self.get_green_time(pcu)
        
        self.lane_data[lane_name] = {
            "count": count,
            "pcu": round(pcu, 2),
            "green_time": round(green_time)
        }

    def tick(self):
        """
        Main state machine logic. Call this in a loop.
        Returns the current state of the intersection.
        """
        now = time.time()
        dt = now - self.last_update_time
        self.last_update_time = now
        
        self.timer -= dt
        
        if self.timer <= 0:
            if self.state == "GREEN":
                self.state = "YELLOW"
                self.timer = self.yellow_duration
            elif self.state == "YELLOW":
                self.state = "ALL_RED"
                self.timer = self.all_red_duration
            elif self.state == "ALL_RED":
                # Move to next phase
                self.current_phase_index = (self.current_phase_index + 1) % 4
                self.state = "GREEN"
                # Get the pre-calculated green time for this new lane
                current_lane = self.phases[self.current_phase_index]
                self.timer = self.lane_data[current_lane]["green_time"]
                
        return self.get_status()

    def get_status(self):
        lanes_status = {}
        cur_lane = self.phases[self.current_phase_index]
        for lane in self.phases:
            lane_state = "RED"
            if lane == cur_lane:
                lane_state = self.state
            
            lanes_status[lane] = {
                **self.lane_data[lane],
                "state": lane_state
            }
            
        return {
            "active_lane": cur_lane,
            "current_state": self.state,
            "timer": max(0, round(self.timer, 1)),
            "lanes": lanes_status
        }
