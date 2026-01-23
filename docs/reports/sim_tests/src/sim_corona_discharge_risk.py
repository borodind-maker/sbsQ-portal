# Copyright (c) 2024-2026 BorodinD&V
# simulations/sim_corona_discharge_risk.py
# Risk Analysis: Corona Discharge & Arc Flash on Drone approaching 110kV Line

import math
import random
import time

class HVEnvironment:
    def __init__(self, voltage_line_kv=110.0):
        # 110kV is Line-to-Line.
        # Phase-to-Ground is V_line / sqrt(3)
        self.v_phase_rms = (voltage_line_kv * 1000.0) / math.sqrt(3)  # ~63,500 V
        self.v_phase_peak = self.v_phase_rms * math.sqrt(2) # ~89,800 V
        self.wire_radius_m = 0.0075 # 15mm diameter
        
        # Breakdown strength of air (approx 30 kV/cm = 3,000,000 V/m)
        # Varies with temp, humidity, pressure.
        self.e_breakdown_air = 3e6 

    def get_ambient_e_field(self, dist_m):
        """
        Calculate E-field (V/m) at distance dist_m from wire center.
        Simplified cylindrical field: E = V / (r * ln(D_ground/r_wire))
        Taking D_ground ~ 10m effectively for the log term.
        """
        dist_m = max(dist_m, self.wire_radius_m + 0.001)
        # Log factor varies slowly, approx 7-8 for typical lines.
        # Let's compute it dynamically for r=dist_m to Ground=10m
        # Actually E near wire is dominated by the wire geometry.
        # E(r) ~ Q / (2*pi*eps*r). V ~ Q/(2*pi*eps) * ln(...).
        # E(r) ~ V_peak / (r * ln(10.0 / wire_radius))
        
        denom = dist_m * math.log(10.0 / self.wire_radius_m)
        e_field = self.v_phase_peak / denom
        return e_field

class DroneConductivePoints:
    def __init__(self):
        # List of critical points on the drone
        # name: part name
        # radius_mm: curvature radius of the part (sharpness)
        # beta: Field Enhancement Factor (approx 1 + 2*L/R for needle-like)
        # For a drone, existing sharp screws/antennas might have beta ~10-50.
        self.parts = [
            {"name": "CarbonFrame_Edge", "beta": 5.0,  "desc": "Standard frame edge"},
            {"name": "Motor_Screw_Head", "beta": 8.0,  "desc": "Exposed bolt"},
            {"name": "Antenna_Tip_Lora", "beta": 35.0, "desc": "Whip antenna tip (Sharp!)"},
            {"name": "Landing_Claw_Tip", "beta": 15.0, "desc": "Metallic gripper tip"},
            {"name": "PCB_Solder_Joint", "beta": 20.0, "desc": "Exposed pin on uncontrolled PCB"}
        ]
        
    def check_corona(self, e_ambient, humidity=0.6):
        """
        Check if any part triggers corona.
        Condition: E_local = E_ambient * beta > E_inception
        E_inception drops with humidity.
        """
        results = []
        # Humidity factor: High humidity lowers breakdown strength slightly,
        # but water droplets on conductors drastically increase local E-field.
        # Let's model breakdown threshold reduction.
        e_limit = 3e6 * (1.0 - 0.2 * (humidity - 0.5)) # Crude adjustment
        
        params = {"max_e_local": 0.0, "danger_part": None}

        for part in self.parts:
            e_local = e_ambient * part["beta"]
            
            is_corona = e_local > e_limit
            
            # Flashover risk (Arc) is much higher threshold, usually if gap is bridged or E is massive
            # Say Arc if E_local > 3 * E_limit
            is_arc = e_local > (3.0 * e_limit)
            
            status = "SAFE"
            if is_corona: status = "CORONA_DISCHARGE"
            if is_arc: status = "ARC_FLASHOVER"
            
            if e_local > params["max_e_local"]:
                params["max_e_local"] = e_local
                params["danger_part"] = part["name"]
                
            results.append({
                "part": part["name"],
                "e_local": e_local,
                "status": status,
                "limit": e_limit
            })
            
        return results, params

def run_corona_sim():
    print("="*100)
    print(f" [HIGH VOLTAGE RISK SIMULATION] CORONA & ARC ANALYSIS")
    print(f" Target: 110 kV Line (Phase-to-Ground ~63.5 kVrms)")
    print("="*100)
    
    env = HVEnvironment(voltage_line_kv=110.0)
    drone = DroneConductivePoints()
    
    # Simulation: Approach from 2m down to contact (0m)
    distances_cm = [200, 100, 50, 30, 20, 15, 10, 5, 2, 1]
    
    print(f"{'Dist(cm)':>8} | {'E_amb(kV/cm)':>12} | {'Max_Part_E(kV/cm)':>18} | {'Critical Part':<20} | {'Status'}")
    print("-" * 100)
    
    safe_approach_limit = 0.0
    
    for d_cm in distances_cm:
        dist_m = d_cm / 100.0
        e_amb = env.get_ambient_e_field(dist_m)
        
        # Apply random environmental noise (humidity patches, dust)
        humidity = 0.6 + random.uniform(-0.1, 0.2)
        
        results, params = drone.check_corona(e_amb, humidity)
        
        # Formatting for log
        # e_amb is V/m. 
        # kV/cm = (V/m) / 1000 / 100 = V/m / 100000
        e_amb_kvcm = e_amb / 100000.0
        e_max_kvcm = params["max_e_local"] / 100000.0
        
        # Determine overall status
        status = "OK"
        for r in results:
            if r["status"] == "ARC_FLASHOVER":
                status = "!!! FLASH !!!"
                break
            if r["status"] == "CORONA_DISCHARGE" and status != "!!! FLASH !!!":
                status = "CORONA (HISS)"
        
        print(f"{d_cm:8.1f} | {e_amb_kvcm:12.2f} | {e_max_kvcm:18.2f} | {params['danger_part']:<20} | {status}")
        
        if status == "CORONA (HISS)" and safe_approach_limit == 0.0:
            safe_approach_limit = d_cm
            
        if status == "!!! FLASH !!!":
             print(f"\n [!!!] CATASTRPHIC FAILURE DETECTED AT {d_cm}cm")
             print(f"       Dielectric breakdown initiated from {params['danger_part']}")
             break
             
    print("="*100)
    print(" MITIGATION RECOMMENDATIONS:")
    print(" 1. Corona Rings: Add toroidal rings around sharp extremities.")
    print(" 2. Antenna Recess: Retract whip antennas or cap with dielectric spheres.")
    print(" 3. Coating: Apply HV insulating varnish to all solder joints/screws.")
    print(f" 4. Safe limit for current design: > {safe_approach_limit} cm")
    print("="*100)

if __name__ == "__main__":
    run_corona_sim()
