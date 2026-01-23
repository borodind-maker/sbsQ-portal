# Copyright (c) 2024-2025 BorodinD&V
# simulations/simulate_hardware_survival.py

import random

class HardwareLogicSim:
    """
    Simulates thermal management and power stability.
    Tests fallback to 'Cooling Mode' and 'Low Power Reserve'.
    """
    def __init__(self):
        self.cpu_temp = 45.0
        self.voltage = 16.8 # 4S Full
        self.throttle_pct = 1.0
        self.is_critical = False

    def cycle(self, ambient_heat, power_draw):
        # 1. Thermal logic
        heat_gain = (power_draw * 0.1) + (ambient_heat * 0.05)
        self.cpu_temp += (heat_gain - 1.5) # 1.5 is cooling efficiency
        
        # 2. Voltage logic
        self.voltage -= (power_draw * 0.001)
        
        # 3. Survival logic (Antigravity Safety Kick)
        if self.cpu_temp > 80.0:
            self.throttle_pct = 0.4 # Force throttle
            self.is_critical = True
        elif self.voltage < 14.0:
            self.throttle_pct = 0.5 # Battery save
            self.is_critical = True
        else:
            self.throttle_pct = 1.0
            self.is_critical = False
            
        return self.throttle_pct

def run_simulation(cycles=1000):
    print("======================================================================")
    print(f" [!] STRESS TEST: HARDWARE SURVIVAL / POWER & THERMAL ({cycles} CYCLES)")
    print(" SCENARIO: AMBIENT 45C + MAX POWER MISSION")
    print("======================================================================")
    
    hw = HardwareLogicSim()
    throttle_events = 0

    for step in range(1, cycles + 1):
        # High load mission
        power = 15.0 + random.uniform(-2, 5)
        throttle = hw.cycle(45.0, power)
        
        if throttle < 1.0: throttle_events += 1
        
        if step % 200 == 0:
            print(f"  Cycle {step}: Temp={hw.cpu_temp:.1f}C | Volt={hw.voltage:.2f}V | Throttle={throttle*100:.0f}%")

    print("\n======================================================================")
    print(" [+] HARDWARE SURVIVAL SUMMARY")
    print(f" FINAL TEMP:    {hw.cpu_temp:.1f}C")
    print(f" SURVIVAL RATE: {100 - (throttle_events/cycles)*100:.1f}% Full Perf")
    print(f" FAIL-SAFE:     {'ACTIVE' if throttle_events > 0 else 'INACTIVE'}")
    print("======================================================================")

if __name__ == "__main__":
    run_simulation(1000)
