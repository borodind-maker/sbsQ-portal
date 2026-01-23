# Copyright (c) 2024-2026 BorodinD&V
# simulations/sim_physics_wire_landing.py
# Refined for LEP 110kV Inductive Charging with Detailed Physics & Safety constraints

import math
import random
import sys
import statistics
import time
from typing import Dict, List, Tuple

# ==============================================================================
# 1. CORE CONSTANTS & MATH
# ==============================================================================

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PI = math.pi
MU_0 = 4 * PI * 1e-7  # Magnetic permeability of vacuum

# Safety & Geometry Constants
SAFETY_DIST_110KV_BELOW = 7.5  # meters (Simulated Legal Limit)
SAFETY_DIST_110KV_SIDE = 9.5   # meters
WIRE_RADIUS_AC120 = 0.0075     # 15mm diameter
FUNNEL_CAPTURE_RADIUS = 0.15   # 15cm mechanical capture range
MAG_SATURATION_THRESHOLD = 500e-6 # 500 uT

# ==============================================================================
# 2. PHYSICS MODELS
# ==============================================================================

class LEP110kV:
    """
    Simulation of a 110kV Transmission Line Physics.
    Focus: Magnetic Field B(r, I) and Electrical Safety Zones.
    """
    def __init__(self, current_rms=450.0, frequency=50.0):
        self.current_rms = current_rms  # Amperes (Source of Induction)
        self.frequency = frequency      # Hz
        self.voltage = 110000.0         # Volts (Source of Danger)
        self.wire_radius = WIRE_RADIUS_AC120

    def get_magnetic_field(self, r: float) -> float:
        """Calculate B-field magnitude (Tesla) at distance r (m)."""
        eff_r = max(r, self.wire_radius)
        # Biot-Savart / Ampere's Law for long straight conductor
        return (MU_0 * self.current_rms) / (2 * PI * eff_r)

    def get_safety_status(self, dy: float, dz: float) -> str:
        """Return regulatory status based on position relative to wire."""
        dist = math.hypot(dy, dz)
        if dist < self.wire_radius + 0.05:
            return "CONTACT_ZONE"
        if dz > -SAFETY_DIST_110KV_BELOW and abs(dy) < SAFETY_DIST_110KV_SIDE:
            return "DANGER_HV_ZONE" # Requires Consent
        return "SAFE_ZONE"

class MagneticGripper:
    """
    Split-Core Current Transformer Model.
    Power depends on Current, Core Permeability, and AIR GAP.
    """
    def __init__(self, turns=600, area=0.002, mu_r=2000):
        self.turns = turns
        self.area = area      # Cross-section (m2)
        self.mu_r = mu_r      # Ferrite permeability
        self.gap_mm = 10.0    # Current mechanical gap (starts open)
        
    def get_inductance_factor(self) -> float:
        """
        Magnetic Reluctance logic:
        Reluctance R = l_core/(mu0*mu_r*A) + l_gap/(mu0*A)
        Power efficiency drops drastically with gap.
        """
        l_core = 0.2 # 20cm circumference
        # Simplify to an efficiency factor 0.0 to 1.0 based on gap
        # When gap is 0, factor is 1.0. When gap is large, factor -> 0.
        # This is a critical non-linear behavior for landing.
        
        reluctance_core = l_core / (MU_0 * self.mu_r * self.area)
        reluctance_gap = (self.gap_mm / 1000.0) / (MU_0 * self.area) # Air has mu_r=1
        
        flux_factor = reluctance_core / (reluctance_core + reluctance_gap)
        return flux_factor

    def calculate_power(self, lep: LEP110kV) -> float:
        """Calculate harvested power in Watts."""
        flux_factor = self.get_inductance_factor()
        
        # Theoretical Max Power (clamped, saturated) ~150W for this size
        # P ~ (I_induced)^2 * R_load
        # I_induced ~ flux
        
        # Simplified model: 
        # Base max power at this line current
        max_theoretical_power = (lep.current_rms / 400.0) * 140.0 
        
        # Efficiency scales with flux factor squared (P = I^2 R)
        efficiency = flux_factor ** 2
        
        # Core saturation check 
        if lep.current_rms > 600:
            efficiency *= 0.9 # Saturation losses
            
        return max_theoretical_power * efficiency

# ==============================================================================
# 3. DRONE & SENSORS
# ==============================================================================

class SensorSuite:
    """
    Simulates sensor noise and limitations near HV lines.
    """
    def __init__(self):
        self.cam_valid = False
        self.mag_jammed = False
        
    def read_mag(self, true_y, b_field_tesla):
        """
        Magnetometer reading. Jams if B-field is too high.
        """
        noise_floor = 0.05 # Base noise in meters equivalent for heading
        if b_field_tesla > MAG_SATURATION_THRESHOLD:
            self.mag_jammed = True
            # Massive noise, effectively useless
            return true_y + random.gauss(0, 5.0) 
        else:
            self.mag_jammed = False
            # Noise scales with B-field even before saturation
            induced_noise = b_field_tesla * 1000.0 
            return true_y + random.gauss(0, noise_floor + induced_noise)

    def read_visual(self, true_y, dist_to_wire):
        """
        Visual Servo (Camera). Precision increases as we get closer.
        Limitations: Motion blur, perspective.
        """
        # Pixel error converts to meter error.
        # Far: 1px = 10cm. Close: 1px = 1mm.
        spatial_res = max(0.001, dist_to_wire * 0.005) # 0.5% angular error
        
        noise = random.gauss(0, spatial_res)
        self.cam_valid = True # Assume good lighting for sim
        return true_y + noise

class DronePhysics:
    def __init__(self):
        self.y = 2.0  # Start 2m offset
        self.z = -8.0 # Start 8m below (entering HV zone)
        self.vy = 0.0
        self.vz = 0.0
        self.mass = 2.5
        self.latched = False
        self.battery_j = 50000.0
        
        # PID State
        self.integ_y = 0.0
        self.last_err_y = 0.0
        self.integ_z = 0.0
        self.last_err_z = 0.0

    def update(self, dt, fy, fz, wind_gust, funnel_assist=False):
        if self.latched:
            self.vy = 0; self.vz = 0; self.y = 0; self.z = 0
            return

        # Forces
        drag = 0.8
        ay = (fy + wind_gust - drag*self.vy) / self.mass
        az = (fz - 9.81 * self.mass - drag*self.vz) / self.mass
        
        # Mechanical Funnel Effect:
        # If we are close (within funnel radius), the guide rails force us rapidly to center
        if funnel_assist:
            # Simulated mechanical force pushing to y=0, z=0
            ay += (-self.y * 50.0)
            az += (-self.z * 50.0)

        self.vy += ay * dt
        self.vz += az * dt
        self.y += self.vy * dt
        self.z += self.vz * dt

    def get_pid_control(self, dt, target_y, target_z):
        # Tuned for "Heavy" drone
        kp_y, ki_y, kd_y = 4.0, 0.05, 2.5
        kp_z, ki_z, kd_z = 6.0, 0.1, 3.0
        
        err_y = target_y - self.y
        d_y = (err_y - self.last_err_y)/dt
        self.integ_y += err_y*dt
        fy = kp_y*err_y + ki_y*self.integ_y + kd_y*d_y
        
        err_z = target_z - self.z
        d_z = (err_z - self.last_err_z)/dt
        self.integ_z += err_z*dt
        fz = kp_z*err_z + ki_z*self.integ_z + kd_z*d_z + (9.81 * self.mass) # Gravity feedforward
        
        self.last_err_y = err_y
        self.last_err_z = err_z
        
        return fy, fz

# ==============================================================================
# 4. MAIN SIMULATION LOOP
# ==============================================================================

def run_landing_simulation():
    print(f"{'='*80}")
    print(f"{'SBSQ NOMADIC DRONE: 110kV WIRE LANDING SIMULATION':^80}")
    print(f"{'Physics Engine: Cur-Driven B-Field | Sensor: Vis+Mag | Safety: Strict':^80}")
    print(f"{'='*80}\n")
    
    # Init Objects
    lep = LEP110kV()
    drone = DronePhysics()
    gripper = MagneticGripper()
    sensors = SensorSuite()
    
    dt = 0.02 # 50Hz control loop
    sim_time = 0.0
    
    print(f"{'TIME':<6} | {'DIST':<6} | {'ZONE':<12} | {'MAG':<8} | {'VIS_ERR':<8} | {'GAP':<6} | {'POWER':<6} | {'EVENT'}")
    print("-" * 100)
    
    approached_hv = False
    
    while sim_time < 60.0:
        # 1. External Factors
        wind = random.gauss(0, 0.5) # Modest wind
        raw_dist = math.hypot(drone.y, drone.z)
        
        # 2. Physics Update
        b_field = lep.get_magnetic_field(raw_dist)
        safety_status = lep.get_safety_status(drone.y, drone.z)
        
        if safety_status == "DANGER_HV_ZONE" and not approached_hv:
            print(f"{sim_time:6.2f} | {raw_dist:6.2f} | {safety_status:<12} | [WARNING] ENTERING CONTROLLED AIRSPACE (7.5m)")
            approached_hv = True
            
        # 3. Sensor Reading
        sens_y_mag = sensors.read_mag(drone.y, b_field)
        sens_y_vis = sensors.read_visual(drone.y, raw_dist)
        
        # Fusion Logic (Mag is ignored if jammed or close)
        # In this sim, we switch to PURE VISUAL when < 2.0m
        if raw_dist < 2.0 or sensors.mag_jammed:
            est_y = sens_y_vis
            nav_mode = "VIS"
        else:
            # Weighted average
            est_y = 0.2*sens_y_mag + 0.8*sens_y_vis
            nav_mode = "HYB"
            
        # 4. Control Logic & Mechanical Funnel
        # Target is always (0,0) - the wire
        # If we are very close, mechanical funnel takes over
        in_funnel = raw_dist < FUNNEL_CAPTURE_RADIUS
        
        fy, fz = drone.get_pid_control(dt, 0.0, 0.0) # Aim for wire
        drone.update(dt, fy, fz, wind, funnel_assist=in_funnel)
        
        # 5. Gripper Logic
        if in_funnel and not drone.latched:
            # Try to close gripper
            # Simulate mechanical closing time (closing gap)
            closing_speed = 50.0 # mm/s
            gripper.gap_mm = max(0.0, gripper.gap_mm - closing_speed * dt)
            
            if gripper.gap_mm < 0.5 and math.hypot(drone.y, drone.z) < 0.02:
                drone.latched = True
                gripper.gap_mm = 0.0
                print(f"{sim_time:6.2f} | {raw_dist:6.2f} | {'LATCHED':<12} | -------- | -------- | {0.0:<6} | ----   | *** MECHANICAL LOCK ***")

        # 6. Power Harvest (Only when latched/close)
        power_w = 0.0
        if drone.latched:
            power_w = gripper.calculate_power(lep)
            drone.battery_j += power_w * dt
            
        # 7. Logging (Throttled)
        if int(sim_time/dt) % 50 == 0:
            mag_state = "JAM" if sensors.mag_jammed else "OK"
            vis_err_mm = abs(est_y - drone.y) * 1000
            print(f"{sim_time:6.2f} | {raw_dist:6.2f} | {safety_status[:12]:<12} | {mag_state:<8} | {vis_err_mm:6.1f}mm | {gripper.gap_mm:6.1f} | {power_w:6.1f} | {nav_mode}")

        sim_time += dt
        
        if drone.latched and drone.battery_j > 50500: # Short charge conservation
             print(f"{sim_time:6.2f} | {0.0:6.2f} | {'CHARGED':<12} | -------- | -------- | {0.0:<6} | {power_w:6.1f} | *** BATTERY TOP-UP OK ***")
             break
             
    # Final Report
    print("-" * 100)
    print("SIMULATION SUMMARY:")
    print(f"Final State: {'LATCHED' if drone.latched else 'FAILED'}")
    print(f"Max Induction Power: {gripper.calculate_power(lep):.2f} W")
    print(f"Safety Consent Violated: {approached_hv}")
    print(f"Magnetometer Jammed: {sensors.mag_jammed} (Expected Behavior)")

if __name__ == "__main__":
    run_landing_simulation()
