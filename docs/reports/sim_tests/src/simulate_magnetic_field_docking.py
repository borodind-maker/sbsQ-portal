# Copyright (c) 2024-2025 BorodinD&V
# simulations/simulate_magnetic_field_docking.py

import random
import math

class MagneticDockingSim:
    """
    Simulates magnetic field induction sensing for proximity docking.
    Target: Infrastructure (Power lines, base stations).
    """
    def __init__(self):
        self.flux_density = 0.0 # uT
        self.distance = 5.0 # meters
        self.is_locked = False

    def update(self, step):
        # Inverse square law simulation (simplified)
        self.flux_density = 500.0 / (self.distance**2 + 0.1)
        
        # Magnetic navigation logic: move closer to maximize flux
        if self.distance > 0.15: # Docking distance
            self.distance -= 0.05 + random.uniform(-0.01, 0.02)
        else:
            self.is_locked = True
            self.distance = 0.15
            
        return self.flux_density, self.distance

def run_simulation(cycles=1000):
    print("======================================================================")
    print(f" [!] STRESS TEST: MAGNETIC RESONANT DOCKING ({cycles} CYCLES)")
    print(" SCENARIO: HIGH-PRECISION PROXIMITY VIA FIELD INDUCTION")
    print("======================================================================")
    
    sim = MagneticDockingSim()
    max_flux = 0.0

    for step in range(1, cycles + 1):
        flux, dist = sim.update(step)
        max_flux = max(max_flux, flux)
        
        if step % 200 == 0:
            print(f"  Cycle {step}: Flux={flux:.2f}uT | Dist={dist:.3f}m | Locked={sim.is_locked}")

    print("\n======================================================================")
    print(" [+] MAGNETIC INDUCTION SUMMARY")
    print(f" PEAK FLUX:      {max_flux:.2f} uT")
    print(f" FINAL DISTANCE: {sim.distance:.3f} m")
    print(f" LOCK STATUS:    {'SUCCESS' if sim.is_locked else 'FAIL'}")
    print("======================================================================")

if __name__ == "__main__":
    run_simulation(1000)
