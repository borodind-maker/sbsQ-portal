# Copyright (c) 2024-2026 BorodinD&V
# simulations/calcs/calc_safe_voltage_limit.py
# Calculates the Maximum Line Voltage permissible for the UNMODIFIED drone (Beta=35)
# to maintain safety at 2cm distance.

import math

def calculate_safe_voltage():
    # Constants
    # Breakdown of air ~30 kV/cm peak
    # Safety factor 2.0 -> Limit = 15 kV/cm
    E_LIMIT_PEAK_KV_CM = 30.0 
    
    # Drone Geometry
    # Beta = 35 (Sharp Antenna)
    BETA = 35.0
    
    # Distance of closest approach logic
    # We need to survive at 2cm (0.02m) to land.
    DIST_M = 0.02
    
    # Wire geometry
    WIRE_RADIUS = 0.0075 # 15mm
    D_GROUND = 10.0 # m
    
    # Formula:
    # E_local = Beta * E_amb
    # E_amb = V_peak / (dist * ln(D/r))
    #
    # We want E_local < E_LIMIT
    # Beta * V_peak / (dist * ln(D/r)) < E_LIMIT
    #
    # V_peak < (E_LIMIT * dist * ln(D/r)) / Beta
    
    # Denom factor (geometric decay)
    denom = DIST_M * math.log(D_GROUND / WIRE_RADIUS)
    # Note: E_LIMIT is kV/cm, so we must be consistent with units.
    # Let's work in kV and meters.
    # E_LIMIT_KV_M = 30 * 100 = 3000 kV/m
    
    E_LIMIT_KV_M = E_LIMIT_PEAK_KV_CM * 100.0
    
    # Solve for V_peak
    v_peak_max = (E_LIMIT_KV_M * denom) / BETA
    
    # Convert V_peak to V_line_rms (which is what lines are named after, e.g. 110kV)
    # V_peak = V_phase_rms * sqrt(2)
    # V_phase_rms = V_line_rms / sqrt(3)
    # -> V_peak = V_line_rms * sqrt(2)/sqrt(3)
    # -> V_line_rms = V_peak * sqrt(3)/sqrt(2)
    
    v_line_max = v_peak_max * math.sqrt(3) / math.sqrt(2)
    
    print(f"--- SAFETY CALCULATION FOR UNMODIFIED DRONE (Beta={BETA}) ---")
    print(f"Breakdown Limit: {E_LIMIT_PEAK_KV_CM} kV/cm")
    print(f"Approach Dist  : {DIST_M*100} cm")
    print("-" * 50)
    print(f"Max Safe V_peak       : {v_peak_max:.2f} kV")
    print(f"Max Safe Line Voltage : {v_line_max:.2f} kV (RMS)")
    print("-" * 50)
    print("EXISTING GRID STANDARDS CHECK:")
    for std_v in [110.0, 35.0, 10.0, 0.4]:
        status = "SAFE" if std_v < v_line_max else "DANGER (Flashover)"
        print(f"  {std_v:5.1f} kV Line : {status}")

if __name__ == "__main__":
    calculate_safe_voltage()
