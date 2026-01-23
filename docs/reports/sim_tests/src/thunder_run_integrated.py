# Copyright (c) 2024-2026 BorodinD&V
# simulations/thunder_run_integrated.py
# FINAL INTEGRATION TEST: Physics (Corona) + Brain (Ternary) + EW (Jamming)

import random
import time
import math

# --- 1. PHYSICS LAYER (CORONA & ENV) ---
class HVEnvironment:
    def __init__(self, voltage_kv=110.0):
        self.v_peak = (voltage_kv * 1000 / math.sqrt(3)) * math.sqrt(2) # ~89.8 kV
        self.wire_radius = 0.0075
    
    def get_field_at(self, dist_m):
        if dist_m <= 0: return 999999.0 # Contact/Short
        denom = dist_m * math.log(10.0 / self.wire_radius)
        return (self.v_peak / denom) / 100000.0 # kV/cm

class DroneHardware:
    def __init__(self, modified=False):
        # Modified = True applies the recommendations from your report
        self.is_modified = modified
        self.antenna_beta = 3.0 if modified else 35.0 # 35 = Sharp tip, 3 = Dielectric Sphere
        self.frame_beta = 5.0
        self.battery = 40.0
        self.integrity = 100.0

    def check_survival(self, dist_m, e_amb_kvcm):
        # 1. Corona Check
        e_local_ant = e_amb_kvcm * self.antenna_beta
        
        status = "OK"
        warning = ""
        
        # Breakdown threshold for air is approx 30 kV/cm
        if e_local_ant > 30.0: 
            if e_local_ant > 200.0: # Flashover
                self.integrity = 0.0
                return "DEAD (ARC_FLASHOVER)"
            else:
                warning = " [HISSING]" # Corona noise
                
        # 2. Charging Logic (Only if docked/very close)
        if dist_m < 0.01 and self.integrity > 0:
            return "DOCKED"
            
        return f"FLYING{warning}"

# --- 2. INTELLIGENCE LAYER (BRAIN) ---
class TernaryBrain:
    def __init__(self):
        self.state = "APPROACH" # APPROACH -> DOCKING -> DREAMING -> DEPART
        self.target_dist = 0.25 # 25cm standoff
        self.decision_log = []
        
    def process_frame(self, dist_m, ew_level, hardware_status):
        # Ternary Logic: -1 (Abort), 0 (Hold/Neutro), +1 (Commit)
        decision = 0 
        action = "HOVER"
        
        # SENSOR FUSION INPUTS
        # EW Level 0.0-1.0 (1.0 = Total Jamming)
        
        if self.state == "APPROACH":
            if hardware_status == "DEAD (ARC_FLASHOVER)":
                return "TERMINATED"
            
            # If EW is high, rely on visual/magnetic gradient, ignore GPS
            if ew_level > 0.8:
                self.decision_log.append("EW_HIGH_SWITCH_TO_OPTICAL")
            
            # Guidance
            err = dist_m - 0.005 # Target 5mm for contact
            if err > 0.5: action = "FAST_FORWARD"
            elif err > 0.05: action = "PRECISION_CREEP"
            else: 
                action = "INITIATE_GRIP"
                self.state = "DOCKING"

        elif self.state == "DOCKING":
            if hardware_status == "DOCKED":
                self.state = "DREAMING"
                action = "ENGAGE_SLEEP_CYCLE"
            else:
                action = "RETRY_GRIP"

        elif self.state == "DREAMING":
            # Simulation of cognitive recuperation
            action = "CHARGING_AND_SYNTHESIZING"
            # Exit condition handled by battery level in main loop

        return action

# --- 3. SIMULATION LOOP ---
def run_thunder_run():
    print("="*60)
    print(" [THUNDER RUN] OPERATION: INTEGRATED TEST")
    print("    Scenario: Penetration via 110kV Power Line")
    print("    Config: MODIFIED HARDWARE (Dielectric Caps Installed)")
    print("="*60)
    
    # Init System
    # !!! IMPORTANT: modified=True based on your report recommendations !!!
    drone = DroneHardware(modified=True) 
    env = HVEnvironment()
    brain = TernaryBrain()
    
    dist_m = 10.0 # Start 10m away
    ew_storm_active = False
    
    print(f"{'T(s)':>5} | {'Dist(cm)':>8} | {'E_local(kV/cm)':>14} | {'EW_Load':>7} | {'Action':<20} | {'Status'}")
    print("-" * 80)

    for t in range(0, 30):
        # 1. Update Physics Position based on previous action (simplified)
        if brain.state == "APPROACH":
            dist_m *= 0.7 # Closing in
        elif brain.state == "DOCKING":
            dist_m = 0.005 # 5mm
        elif brain.state == "DREAMING":
            dist_m = 0.0 # Contact
            drone.battery += 5.0 # Charge
            
        # 2. Generate Threats
        # Random EW Burst
        ew_level = random.uniform(0.0, 0.3)
        if t > 5 and t < 10: 
            ew_level = 0.95 # MASSIVE JAMMING ATTACK during approach
            ew_storm_active = True
        
        # 3. Calculate Physics Risks
        e_amb = env.get_field_at(dist_m)
        status = drone.check_survival(dist_m, e_amb)
        
        # E_local for display (Antenna Tip)
        e_local_display = e_amb * drone.antenna_beta
        
        if status == "DEAD (ARC_FLASHOVER)":
            print(f"{t:5d} | {dist_m*100:8.1f} | {e_local_display:14.2f} | {ew_level:7.2f} | {'---':<20} | !!! CATASTROPHIC FAILURE")
            break

        # 4. Brain Processing
        action = brain.process_frame(dist_m, ew_level, status)
        
        # Log Output
        print(f"{t:5d} | {dist_m*100:8.1f} | {e_local_display:14.2f} | {ew_level:7.2f} | {action:<20} | {status}")
        
        if drone.battery >= 100.0 and brain.state == "DREAMING":
            print("-" * 80)
            print(" [BATTERY FULL] INSTINCTS UPDATED. DETACHING...")
            break
            
        time.sleep(0.05) # Speed up slightly for test

    print("="*60)
    if drone.integrity > 0:
        print(" [MISSION SUCCESS] Logic held, Hardware survived.")
    else:
        print(" [MISSION FAILED] integrity lost.")

if __name__ == "__main__":
    run_thunder_run()
