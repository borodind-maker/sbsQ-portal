"""Quick runner for clean baseline (no injections)"""
from mass_stress_test_chi2_v2_calibrated import GlobalSimulationRunner

class NoInjectionRunner(GlobalSimulationRunner):
    def _inject_anomalies(self, prediction, measurement, sigma_meas, sigma_pred, noise_factor):
        return False, "NONE"  # Disable all injections

if __name__ == "__main__":
    import sys
    runner = NoInjectionRunner(
        cycles=100000,
        mode="nominal",
        seed=42,
        allowed_dof=(2, 3, 6, 9),
        print_every=10000
    )
    runner.run()
