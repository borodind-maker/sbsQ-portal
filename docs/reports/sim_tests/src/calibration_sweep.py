"""
Sigma Calibration Sweep — знаходить оптимальний множник для sigma_meas
щоб ACCEPT у baseline (без ін'єкцій) наближався до теоретичних 89.43%
"""
import sys
import os

# Додаємо шлях до v2 скрипту
sys.path.insert(0, os.path.dirname(__file__))

from mass_stress_test_chi2_v2 import GlobalSimulationRunner, clamp
import statistics


def run_calibration_sweep(cycles_per_k: int = 10000, dof_list=(3, 6, 9)):
    """
    Прогоняє симуляцію з різними множниками для sigma_meas
    Шукає k такий, що baseline ACCEPT ≈ 89.43%
    """
    
    # Діапазон множників для sigma_meas
    k_values = [1.0, 1.2, 1.5, 1.8, 2.0, 2.5]
    
    print("="*100)
    print(" SIGMA CALIBRATION SWEEP - TARGET: ACCEPT ~89.43% (baseline, no injections)")
    print("="*100)
    print(f" Cycles per k: {cycles_per_k}")
    print(f" DOF tested: {dof_list}")
    print(f" k values: {k_values}")
    print("="*100)
    print()
    
    results = {}
    
    for dof in dof_list:
        print(f"\n{'-'*100}")
        print(f" Testing DOF = {dof}")
        print(f"{'-'*100}\n")
        
        results[dof] = {}
        
        for k in k_values:
            print(f"  [k={k:.2f}] Running {cycles_per_k} cycles...")
            
            # Модифікуємо runner щоб використовувати k
            # Тимчасове рішення: передаємо через mode override
            runner = CalibratedRunner(
                cycles=cycles_per_k,
                mode="nominal",
                seed=42,
                allowed_dof=(dof,),
                print_every=cycles_per_k + 1,  # No console spam
                sigma_meas_mult=k,
                injection_disabled=True  # БЕЗ ін'єкцій для baseline
            )
            
            runner.run()
            
            acc = runner.stats["ACCEPTED"]
            unk = runner.stats["UNKNOWN"]
            rej = runner.stats["REJECTED"]
            
            accept_pct = (acc / cycles_per_k) * 100.0
            unknown_pct = (unk / cycles_per_k) * 100.0
            reject_pct = (rej / cycles_per_k) * 100.0
            
            results[dof][k] = {
                "accept_pct": accept_pct,
                "unknown_pct": unknown_pct,
                "reject_pct": reject_pct,
                "delta_from_target": abs(accept_pct - 89.43)
            }
            
            # Color for closeness to target
            delta = results[dof][k]["delta_from_target"]
            status = "+++" if delta < 2.0 else "++" if delta < 5.0 else "+" if delta < 10.0 else "X"
            
            print(f"    ACCEPT: {accept_pct:6.2f}% | UNKNOWN: {unknown_pct:6.2f}% | REJECT: {reject_pct:6.2f}% | Delta={delta:5.2f}% {status}")
    
    # Summary
    print(f"\n{'='*100}")
    print(" CALIBRATION SUMMARY")
    print(f"{'='*100}\n")
    
    print("  | DOF | k_mult | ACCEPT% | UNKNOWN% | REJECT% | Delta from 89.43% | Recommendation |")
    print("  |----:|-------:|--------:|---------:|--------:|------------------:|:---------------|")
    
    for dof in dof_list:
        best_k = min(results[dof].keys(), key=lambda k: results[dof][k]["delta_from_target"])
        
        for k in k_values:
            r = results[dof][k]
            is_best = (k == best_k)
            rec = "STAR BEST" if is_best else ""
            
            print(f"  | {dof:3d} | {k:6.2f} | {r['accept_pct']:7.2f} | {r['unknown_pct']:8.2f} | {r['reject_pct']:7.2f} | {r['delta_from_target']:13.2f} | {rec:14s} |")
    
    print(f"\n{'='*100}\n")
    
    # Рекомендації
    print("RECOMMENDATIONS:")
    for dof in dof_list:
        best_k = min(results[dof].keys(), key=lambda k: results[dof][k]["delta_from_target"])
        best_accept = results[dof][best_k]["accept_pct"]
        print(f"  * DOF={dof}: Use sigma_meas_mult = {best_k:.2f} -> ACCEPT = {best_accept:.2f}%")
    
    print()


class CalibratedRunner(GlobalSimulationRunner):
    """
    Extended runner з калібрувальним множником для sigma_meas
    та можливістю вимкнути ін'єкції
    """
    
    def __init__(self, sigma_meas_mult=1.0, injection_disabled=False, **kwargs):
        super().__init__(**kwargs)
        self.sigma_meas_mult = float(sigma_meas_mult)
        self.injection_disabled = injection_disabled
    
    def _rand_sigmas(self, nu, noise_factor):
        """Override: apply calibration multiplier"""
        import random
        sigma_meas = [
            random.uniform(0.5, 2.0) * (noise_factor / 2.0) * self.sigma_meas_mult
            for _ in range(nu)
        ]
        sigma_pred = [random.uniform(0.1, 0.5) for _ in range(nu)]
        return sigma_meas, sigma_pred
    
    def _inject_anomalies(self, prediction, measurement, sigma_meas, sigma_pred, noise_factor):
        """Override: optionally disable injections"""
        if self.injection_disabled:
            return False, "NONE"
        return super()._inject_anomalies(prediction, measurement, sigma_meas, sigma_pred, noise_factor)
    
    def print_summary(self):
        """Suppress verbose output for sweep"""
        pass  # Тиша під час sweep


if __name__ == "__main__":
    import sys
    
    cycles = 10000 if len(sys.argv) < 2 else int(sys.argv[1])
    dof_list = (3, 6, 9) if len(sys.argv) < 3 else tuple(int(x) for x in sys.argv[2].split(","))
    
    run_calibration_sweep(cycles_per_k=cycles, dof_list=dof_list)
