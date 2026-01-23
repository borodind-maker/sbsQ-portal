"""
Adversarial Injection Sweep
Tests detection rates against spoofing attacks of varying magnitudes proportional to sigma.
"""
import sys
import os
import random
import math

# Add path to v2 calibrated script
sys.path.insert(0, os.path.dirname(__file__))

from mass_stress_test_chi2_v2_calibrated import GlobalSimulationRunner

class AdversarialRunner(GlobalSimulationRunner):
    def __init__(self, bias_sigma_mult=3.0, **kwargs):
        super().__init__(**kwargs)
        self.bias_sigma_mult = bias_sigma_mult
        
    def _inject_anomalies(self, prediction, measurement, sigma_meas, sigma_pred, noise_factor):
        # FORCE INJECTION OF SPOOF TYPE ONLY
        injected = True
        anomaly_type = "SPOOF"
        self.stats["INJECTED_SPOOF"] += 1
        self.stats["INJECTED_TOTAL"] += 1

        dims = len(measurement)
        # Inject into random channels
        k = random.randint(1, max(1, dims // 2))
        idxs = random.sample(range(dims), k=k)

        for j in idxs:
            # Scale bias by the injected magnitude AND the local sigma
            # This tests "How many sigmas of error can we catch?"
            sigma_total = math.hypot(sigma_meas[j], sigma_pred[j])
            bias = self.bias_sigma_mult * sigma_total
            measurement[j] += bias * (1.0 if random.random() < 0.5 else -1.0)
            
        return injected, anomaly_type

def run_sweep():
    # Test bias magnitudes from 1.0 sigma to 8.0 sigma
    magnitudes = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0]
    cycles_per_step = 2000 # Enough for stats
    
    print("="*80)
    print(" ADVERSARIAL INJECTION SWEEP (Calibrated Model)")
    print(" Testing detection rate vs. Attack Magnitude (in units of sigma_total)")
    print("="*80)
    print(f" Cycles per step: {cycles_per_step}")
    print("="*80)
    print(" |  Mag (sigma) | DETECTED% | REJECTED% | MISSED% | Status")
    print(" |---------:|----------:|----------:|--------:|:-------")
    
    for mag in magnitudes:
        runner = AdversarialRunner(
            bias_sigma_mult=mag,
            cycles=cycles_per_step,
            mode="nominal",
            seed=42, # Deterministic seed for fair comparison
            allowed_dof=(2, 3, 6, 9),
            print_every=cycles_per_step + 1
        )
        runner.run()
        
        detected = runner.stats["INJECTED_DETECTED"]
        rejected = runner.stats["INJECTED_REJECTED"]
        missed = runner.stats["INJECTED_MISSED"]
        total = runner.stats["INJECTED_TOTAL"]
        
        det_pct = (detected / total) * 100.0
        rej_pct = (rejected / total) * 100.0
        miss_pct = (missed / total) * 100.0
        
        status = "[SECURE]" if det_pct > 95 else "[WEAK]" if det_pct > 50 else "[VULNERABLE]"
        
        print(f" | {mag:8.1f} | {det_pct:9.1f} | {rej_pct:9.1f} | {miss_pct:7.1f} | {status}")

    print("="*80)

if __name__ == "__main__":
    run_sweep()
