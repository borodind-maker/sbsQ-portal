import argparse
import math
import random
import sys
from typing import Dict, Tuple

# --- Constants from Nature Math ---
PHI = (1.0 + math.sqrt(5.0)) / 2.0  # φ ≈ 1.618
PI = math.pi  # π ≈ 3.14159


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


P_PHI_1D = _normal_cdf(PHI) - _normal_cdf(-PHI)
P_PI_1D = _normal_cdf(PI) - _normal_cdf(-PI)
ALPHA1 = 1.0 - P_PHI_1D
ALPHA2 = 1.0 - P_PI_1D

CHI2_QUANTILES_NU_2_9: Dict[int, Tuple[float, float]] = {
    2: (4.495147252343149, 12.777546415481542),
    3: (6.125634554981158, 15.165786345183298),
    4: (7.640877063591785, 17.312786871870735),
    5: (9.086707340510804, 19.313122417323722),
    6: (10.485074899738043, 21.21216156409065),
    7: (11.848416344721059, 23.035788532634136),
    8: (13.184560344926634, 24.800422616899166),
    9: (14.498804274179633, 26.51725541364702),
}

MODE_PRESETS = {
    "default": {"q1_mult": 1.0, "q2_mult": 1.0, "spoof_prob": 0.00, "spoof_bias_mult": 6.0, "unknown_weight": 0.25},
    "cruise": {"q1_mult": 1.0, "q2_mult": 1.2, "spoof_prob": 0.01, "spoof_bias_mult": 6.0, "unknown_weight": 0.35},
    "precision": {"q1_mult": 0.8, "q2_mult": 1.0, "spoof_prob": 0.02, "spoof_bias_mult": 8.0, "unknown_weight": 0.10},
}


class GlobalSimulationRunner:
    """
    Massive Stress Test Runner for sbsQ System Logic (ND Chi-square Gate).
    Executes randomized multi-dimensional residual validation with strict χ² gating
    and a heuristic fallback gate.
    """

    def __init__(
        self,
        cycles: int = 10000,
        dof: int = 6,
        mode: str = "default",
        seed: int | None = None,
        spoof_prob: float | None = None,
        q1_mult: float | None = None,
        q2_mult: float | None = None,
        unknown_weight: float | None = None,
        temp_alpha: float = 1.0,
        t_min: float = 0.0,
        t_max: float = 0.5,
    ):
        self.cycles = int(cycles)
        self.dof = int(dof)
        self.mode = mode if mode in MODE_PRESETS else "default"
        self.seed = seed

        preset = MODE_PRESETS[self.mode]
        self.spoof_prob = float(preset["spoof_prob"] if spoof_prob is None else spoof_prob)
        self.q1_mult = float(preset["q1_mult"] if q1_mult is None else q1_mult)
        self.q2_mult = float(preset["q2_mult"] if q2_mult is None else q2_mult)
        self.unknown_weight = float(preset["unknown_weight"] if unknown_weight is None else unknown_weight)
        self.spoof_bias_mult = float(preset["spoof_bias_mult"])

        self.temp_alpha = float(temp_alpha)
        self.t_min = float(t_min)
        self.t_max = float(t_max)

        self.stats = {
            "ACCEPTED": 0,
            "UNKNOWN": 0,
            "REJECTED": 0,
            "TOTAL_ANOMALIES": 0,
            "CRITICAL_FAILURES": 0,
            "SPOOF_EVENTS": 0,
            "INVALID_EVENTS": 0,
            "FALLBACK_USED": 0,
        }

    def _get_quantiles(self) -> Tuple[float, float] | None:
        base = CHI2_QUANTILES_NU_2_9.get(self.dof)
        if base is None:
            return None
        q1, q2 = base
        return (q1 * self.q1_mult, q2 * self.q2_mult)

    def _clamp(self, x: float, lo: float, hi: float) -> float:
        return lo if x < lo else hi if x > hi else x

    def _temp_schedule(self, m: float) -> float:
        val = self.t_max * math.exp(-self.temp_alpha * m)
        return self._clamp(val, self.t_min, self.t_max)

    def run(self):
        if self.seed is not None:
            random.seed(self.seed)

        quantiles = self._get_quantiles()
        strict_enabled = quantiles is not None

        print(f"{'='*80}")
        print(f" [!] STARTING MASSIVE SYSTEM STRESS TEST: {self.cycles:,} CYCLES")
        print(f" [!] GATE: ND Chi2 (STRICT) + FALLBACK HEURISTIC")
        print(f" [!] MODE: {self.mode} | DOF: {self.dof} | SEED: {self.seed}")
        print(f" [!] 1D COVERAGE: P(|Z|<=PHI)={P_PHI_1D:.6f} -> a1={ALPHA1:.6f} | P(|Z|<=PI)={P_PI_1D:.6f} -> a2={ALPHA2:.6f}")
        if strict_enabled:
            q1, q2 = quantiles
            print(f" [!] Chi2 QUANTILES (nu={self.dof}): q1={q1:.4f} | q2={q2:.4f} | multipliers: q1*x{self.q1_mult:.3f}, q2*x{self.q2_mult:.3f}")
        else:
            print(" [!] Chi2 QUANTILES: unavailable for this nu -> heuristic fallback only")
        print(f" [!] TEMP SCHEDULE: alpha={self.temp_alpha:.3f} | t_min={self.t_min:.3f} | t_max={self.t_max:.3f}")
        print(f"{'='*80}\n")

        for i in range(1, self.cycles + 1):
            noise_factor = random.uniform(0.1, 5.0)

            truth = [random.uniform(10.0, 100.0) for _ in range(self.dof)]

            pred_std = 0.5 * noise_factor
            meas_std = 1.0 * noise_factor

            prediction = [truth[j] + random.gauss(0.0, pred_std) for j in range(self.dof)]
            measurement = [truth[j] + random.gauss(0.0, meas_std) for j in range(self.dof)]

            if random.random() < self.spoof_prob:
                self.stats["SPOOF_EVENTS"] += 1
                idx = random.randrange(self.dof)
                sigma_meas_probe = random.uniform(0.5, 2.0) * (noise_factor / 2.0)
                bias = random.choice([-1.0, 1.0]) * self.spoof_bias_mult * max(sigma_meas_probe, 1e-6)
                measurement[idx] += bias

            sigma_meas = [random.uniform(0.5, 2.0) * (noise_factor / 2.0) for _ in range(self.dof)]
            sigma_pred = [random.uniform(0.1, 0.5) for _ in range(self.dof)]

            sigma_total_sq = [(sigma_meas[j] * sigma_meas[j] + sigma_pred[j] * sigma_pred[j]) for j in range(self.dof)]
            if any((not math.isfinite(v) or v <= 0.0) for v in sigma_total_sq):
                self.stats["INVALID_EVENTS"] += 1
                self.stats["UNKNOWN"] += 1
                self.stats["TOTAL_ANOMALIES"] += 1
                status = "UNKNOWN"
                d2 = float("inf")
                d = float("inf")
                temp = 0.0
            else:
                r = [measurement[j] - prediction[j] for j in range(self.dof)]
                d2 = 0.0
                for j in range(self.dof):
                    d2 += (r[j] * r[j]) / sigma_total_sq[j]
                d = math.sqrt(d2) if d2 >= 0.0 else float("inf")

                status = ""
                temp = self._temp_schedule(d)

                if strict_enabled:
                    q1, q2 = quantiles
                    if d2 <= q1:
                        status = "ACCEPTED"
                        self.stats["ACCEPTED"] += 1
                    elif d2 <= q2:
                        status = "UNKNOWN"
                        self.stats["UNKNOWN"] += 1
                        self.stats["TOTAL_ANOMALIES"] += 1
                    else:
                        status = "REJECTED"
                        self.stats["REJECTED"] += 1
                        self.stats["TOTAL_ANOMALIES"] += 1
                else:
                    self.stats["FALLBACK_USED"] += 1
                    if d <= PHI:
                        status = "ACCEPTED"
                        self.stats["ACCEPTED"] += 1
                    elif d <= PI:
                        status = "UNKNOWN"
                        self.stats["UNKNOWN"] += 1
                        self.stats["TOTAL_ANOMALIES"] += 1
                    else:
                        status = "REJECTED"
                        self.stats["REJECTED"] += 1
                        self.stats["TOTAL_ANOMALIES"] += 1

                if d > 10.0:
                    self.stats["CRITICAL_FAILURES"] += 1

                if status == "REJECTED":
                    temp = 0.0

            if i % 10000 == 0 or i == 1:
                print(
                    f"Cycle {i:7,}: d2={d2:8.3f} | d={d:6.3f} | noise={noise_factor:4.2f} | temp={temp:4.2f} | Result: {status}"
                )

        self.print_summary(strict_enabled=strict_enabled)

    def print_summary(self, strict_enabled: bool):
        accept = self.stats["ACCEPTED"]
        unk = self.stats["UNKNOWN"]
        rej = self.stats["REJECTED"]
        total = self.cycles

        accept_pct = (accept / total) * 100.0
        unk_pct = (unk / total) * 100.0
        rej_pct = (rej / total) * 100.0

        weighted_health = ((accept + self.unknown_weight * unk) / total) * 100.0

        print(f"\n{'='*80}")
        print(f" [!] STRESS TEST SUMMARY ({total:,} CYCLES)")
        print(f"{'='*80}")
        print(f"  GATE MODE:          {'STRICT Chi2' if strict_enabled else 'HEURISTIC'} | nu={self.dof}")
        print(f"  MODE PRESET:        {self.mode} | q1*x{self.q1_mult:.3f} q2*x{self.q2_mult:.3f} | spoof_prob={self.spoof_prob:.3f}")
        print("-" * 80)
        print(f"  ACCEPTED:           {accept:7,} ({accept_pct:6.2f}%)")
        print(f"  UNKNOWN:            {unk:7,} ({unk_pct:6.2f}%)")
        print(f"  REJECTED:           {rej:7,} ({rej_pct:6.2f}%)")
        print("-" * 80)
        print(f"  TOTAL ANOMALIES:    {self.stats['TOTAL_ANOMALIES']:7,}")
        print(f"  CRITICAL FAILURES:  {self.stats['CRITICAL_FAILURES']:7,} (d > 10.0)")
        print(f"  SPOOF EVENTS:       {self.stats['SPOOF_EVENTS']:7,}")
        print(f"  INVALID EVENTS:     {self.stats['INVALID_EVENTS']:7,}")
        print(f"  FALLBACK USED:      {self.stats['FALLBACK_USED']:7,}")
        print("-" * 80)
        print(f"  HEALTH (ACCEPT%):   {accept_pct:6.2f}%")
        print(f"  HEALTH (WEIGHTED):  {weighted_health:6.2f}%  (unknown_weight={self.unknown_weight:.2f})")

        if weighted_health > 90.0:
            status = "STABLE"
        elif weighted_health > 70.0:
            status = "DEGRADED"
        else:
            status = "UNSTABLE"
        print(f"  STATUS:             [{status}]")
        print(f"{'='*80}\n")

        if strict_enabled and self.dof in (2, 3, 6, 9):
            q1, q2 = self._get_quantiles() or (0.0, 0.0)
            print("  PRECOMPUTED Chi2 EXAMPLE TABLE (nu=2,3,6,9) for a1/a2 from PHI/PI coverage:")
            for nu in (2, 3, 6, 9):
                base = CHI2_QUANTILES_NU_2_9[nu]
                print(f"   nu={nu:2d}: q1={base[0]:8.4f} | q2={base[1]:8.4f}")
            print(f"{'='*80}\n")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("cycles", nargs="?", type=int, default=10000)
    p.add_argument("--dof", type=int, default=6)
    p.add_argument("--mode", type=str, default="default", choices=sorted(MODE_PRESETS.keys()))
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--spoof-prob", type=float, default=None)
    p.add_argument("--q1-mult", type=float, default=None)
    p.add_argument("--q2-mult", type=float, default=None)
    p.add_argument("--unknown-weight", type=float, default=None)
    p.add_argument("--temp-alpha", type=float, default=1.0)
    p.add_argument("--t-min", type=float, default=0.0)
    p.add_argument("--t-max", type=float, default=0.5)
    return p.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args(sys.argv[1:])
    runner = GlobalSimulationRunner(
        cycles=args.cycles,
        dof=args.dof,
        mode=args.mode,
        seed=args.seed,
        spoof_prob=args.spoof_prob,
        q1_mult=args.q1_mult,
        q2_mult=args.q2_mult,
        unknown_weight=args.unknown_weight,
        temp_alpha=args.temp_alpha,
        t_min=args.t_min,
        t_max=args.t_max,
    )
    runner.run()
