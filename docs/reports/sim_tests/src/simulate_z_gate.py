import math

# Constants from Nature Math
PHI = (1.0 + math.sqrt(5.0)) / 2.0        # φ ≈ 1.6180339887
INV_PHI = 1.0 / PHI                        # 1/φ ≈ 0.6180339887
PI = math.pi                               # π

class HarmonyGatePhysics:
    def __init__(self, accept_k=PHI, unknown_k=PI, unit="m"):
        self.cycle_count = 0
        self.accept_k = float(accept_k)
        self.unknown_k = float(unknown_k)
        self.unit = str(unit)

        if self.accept_k <= 0.0 or self.unknown_k <= 0.0 or self.accept_k >= self.unknown_k:
            raise ValueError("Invalid thresholds: require 0 < accept_k < unknown_k")

    def evaluate(self, x_pred, x_meas, sigma_meas, sigma_pred=0.0):
        self.cycle_count += 1

        delta = abs(x_meas - x_pred)

        # Total uncertainty: include both measurement noise and prediction/model uncertainty
        sigma_total = math.hypot(float(sigma_meas), float(sigma_pred))

        status = "UNKNOWN"
        action = "WAIT"

        if not math.isfinite(sigma_total) or sigma_total <= 0.0:
            z = float("inf")
            status = "[X] INVALID"
            action = "BLOCK (INVALID SIGMA)"
        else:
            z = delta / sigma_total

            if z <= self.accept_k:
                status = "[OK] ACCEPT"
                action = "COMMIT TO MAP"
            elif z <= self.unknown_k:
                status = "[?] UNKNOWN"
                action = "LOWER TEMP & RE-SCAN"
            else:
                status = "[X] REJECT"
                action = "BLOCK (HALLUCINATION)"

        return {
            "Cycle": self.cycle_count,
            "Pred": f"{x_pred:.3f}{self.unit}",
            "Meas": f"{x_meas:.3f}{self.unit}",
            "Delta": f"{delta:.3f}{self.unit}",
            "SigmaMeas": f"{float(sigma_meas):.3f}{self.unit}",
            "SigmaPred": f"{float(sigma_pred):.3f}{self.unit}",
            "SigmaTotal": f"{sigma_total:.3f}{self.unit}" if math.isfinite(sigma_total) else f"{sigma_total}",
            "Z-Score": f"{z:.4f}" if math.isfinite(z) else f"{z}",
            "Gate": status,
            "Action": action
        }

# Simulation Setup
gate = HarmonyGatePhysics(accept_k=PHI, unknown_k=PI, unit="m")

print(f"{'#'*80}")
print("RUNNING PHYSICS-BASED THRESHOLD SIMULATION (10 CYCLES)")
print(f"Rules: Z <= PHI({PHI:.3f}) -> OK | Z <= PI({PI:.3f}) -> UNK | Z > PI -> REJECT")
print("Note: sigma_total = sqrt(sigma_meas^2 + sigma_pred^2)")
print(f"{'#'*80}\n")

headers = ["Cycle", "Pred", "Meas", "Delta", "SigmaMeas", "SigmaPred", "SigmaTotal", "Z-Score", "Gate", "Action"]
row_format = "{:<6} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<15} {:<20}"
print(row_format.format(*headers))
print("-" * 120)

# Scenarios: (x_pred, x_meas, sigma_meas, sigma_pred)
scenarios = [
    (100.0, 100.2, 0.5, 0.0),   # Z=0.4 -> ACCEPT
    (100.0, 100.5, 0.5, 0.0),   # Z=1.0 -> ACCEPT (<= \u03c6)
    (100.0, 100.3, 0.5, 0.0),   # Z=0.6 -> ACCEPT
    (100.0, 102.0, 0.5, 0.0),   # Z=4.0 -> REJECT (> \u03c0)
    (100.0, 101.5, 0.5, 0.0),   # Z=3.0 -> UNKNOWN (<= \u03c0)
    (100.0, 100.1, 0.1, 0.0),   # Z=1.0 -> ACCEPT
    (100.0, 105.0, 2.0, 0.0),   # Z=2.5 -> UNKNOWN
    (100.0, 110.0, 2.0, 0.0),   # Z=5.0 -> REJECT
    (50.0,  50.05, 0.1, 0.0),   # Z=0.5 -> ACCEPT
    (50.0,  50.62, 0.2, 0.2),   # includes model uncertainty -> sigma_total=0.283, Z~2.19 -> UNKNOWN
]

for s in scenarios:
    res = gate.evaluate(s[0], s[1], s[2], s[3])
    print(row_format.format(
        res["Cycle"], res["Pred"], res["Meas"], res["Delta"],
        res["SigmaMeas"], res["SigmaPred"], res["SigmaTotal"],
        res["Z-Score"], res["Gate"], res["Action"]
    ))
