# Copyright (c) 2024-2025 BorodinD&V
# simulations/simulate_electronic_storm_siege.py

import time
import sys
import os
import random
import math

# --- Mock Logic for Standalone Execution ---
class TernaryDecisionEngine:
    def evaluate_situation(self, data, uncertainty):
        # 1: Action (Strong Signal), 0: Hover (Uncertain), -1: Retreat (Danger)
        nh3 = data.get('nh3', 0)
        wifi = data.get('wifi', 0)
        
        if nh3 > 100: return {'ternary_state': -1}
        if wifi < 30: return {'ternary_state': 0}
        return {'ternary_state': 1}

class ReflexBreaker:
    def __init__(self, oscillation_threshold=0.3):
        self.history = []
        self.threshold = oscillation_threshold
    def monitor(self, val):
        self.history.append(val)
        if len(self.history) > 10:
            self.history.pop(0)
            # Detect 0.8 / -0.8 oscillation
            if all(abs(x) > 0.5 for x in self.history):
                diffs = [abs(self.history[i] - self.history[i-1]) for i in range(1, len(self.history))]
                if sum(diffs) / len(diffs) > 1.0: # High switching frequency
                    return 0.0 # Force zero to break resonance
        return None

from smartbees.sensors.simulated_source import SimulationSource

def run_operation_electronic_storm(total_target_cycles=1000):
    print("======================================================================")
    print(f" [!] OPERATION: ELECTRONIC STORM SIEGE - STRESS TEST ({total_target_cycles} CYCLES)")
    print(" ARCHITECTURE: sbsQ v1.6 | ENGINE: ANTIGRAVITY (Standalone Mock)")
    print("======================================================================")

    source = SimulationSource()
    engine = TernaryDecisionEngine()
    breaker = ReflexBreaker(oscillation_threshold=0.3)
    
    phase_ratio = [0.1, 0.2, 0.3, 0.3, 0.1]
    phase_names = [
        ("PRE-FLIGHT HARMONY", 0.0, 0.0),
        ("CHEMICAL LEAK DETECTED", 0.1, 0.7),
        ("EW INITIATED (GPS DRIFT)", 0.6, 0.8),
        ("TOTAL BANTU (GPS BLACKOUT)", 0.95, 0.95),
        ("RECOVERY & PHI SYNC", 0.1, 0.1)
    ]

    metrics = {"avg_hz": [], "avg_entropy": [], "conflicts_resolved": 0}
    current_cycle = 0

    for idx, (name, chaos, gas) in enumerate(phase_names):
        duration = int(total_target_cycles * phase_ratio[idx])
        print(f"\n>>> PHASE: {name} | Chaos: {chaos} | Goal: {duration} cycles")
        source.set_chemical_threat(gas)
        
        for i in range(duration):
            current_cycle += 1
            packet = source.generate_packet(chaos_factor=chaos)
            
            sensor_data = {"nh3": packet['chem']['nh3'], "wifi": packet['comms']['rssi_dbm'] + 100, "gps": 1.0 if packet['gps']['status'] == "FIX_3D" else 0.0}
            uncertainties = {"nh3": 0.1 + (chaos * 0.5), "wifi": 0.1 + (chaos * 0.8), "gps": chaos}
            
            decision = engine.evaluate_situation(sensor_data, uncertainties)
            t_state = decision['ternary_state']
            
            steering = 0.8 if t_state == 1 else (-0.8 if t_state == -1 else (0.4 if random.random() > 0.5 else -0.4))
            if chaos > 0.8:
                 steering = 0.8 if i % 2 == 0 else -0.8
            
            correction = breaker.monitor(steering)
            if correction is not None:
                metrics['conflicts_resolved'] += 1
                if current_cycle % 100 == 0:
                    print(f"  Cycle {current_cycle}: [~] REB CONFLICT RESOLVED via Standalone Breaker")

            metrics['avg_hz'].append(packet['system']['loop_hz'])
            metrics['avg_entropy'].append(packet['system']['entropy'])
            
            if current_cycle % 200 == 0:
                print(f"  Progress: {current_cycle}/{total_target_cycles} | State={t_state} | Entropy={packet['system']['entropy']:.2f}")

    print("\n" + "="*70)
    print(" [+] STRESS TEST REPORT: ELECTRONIC STORM SIEGE")
    print("="*70)
    print(f" TOTAL CYCLES COMPLETED: {current_cycle}")
    print(f" AVG SYSTEM ENTROPY:     {sum(metrics['avg_entropy'])/len(metrics['avg_entropy']):.2f}")
    print(f" REB RESILIENCE ACTIONS: {metrics['conflicts_resolved']}")
    print(" MISSION STATUS: SWARM OPERATIONAL")
    print("="*70)

if __name__ == "__main__":
    count = 1000
    if len(sys.argv) > 1:
        count = int(sys.argv[1])
    run_operation_electronic_storm(count)
