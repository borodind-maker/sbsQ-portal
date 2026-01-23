import random
import math
import sys
import statistics
from typing import Dict, List, Tuple, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PI = math.pi

P_COVER_PHI_1D = 0.8943
P_COVER_PI_1D = 0.9983
ALPHA_1 = 1.0 - P_COVER_PHI_1D
ALPHA_2 = 1.0 - P_COVER_PI_1D

DEFAULT_ALLOWED_DOF = (2, 3, 6, 9)

PRECOMPUTED_CHI2_QUANTILES = {
    2: {"q1": 4.4951, "q2": 12.7775},
    3: {"q1": 6.1256, "q2": 15.1658},
    6: {"q1": 10.4851, "q2": 21.2122},
    9: {"q1": 14.4988, "q2": 26.5173},
}


def chi2_quantile_wilson_hilferty(df: int, p: float) -> float:
    if df <= 0:
        return float("inf")
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return float("inf")
    z = statistics.NormalDist().inv_cdf(p)
    a = 2.0 / (9.0 * df)
    t = 1.0 - a + z * math.sqrt(a)
    if t <= 0.0:
        return 0.0
    return df * (t ** 3)


def get_chi2_thresholds(df: int, alpha1: float, alpha2: float) -> Tuple[float, float, bool]:
    if df in PRECOMPUTED_CHI2_QUANTILES:
        q = PRECOMPUTED_CHI2_QUANTILES[df]
        return float(q["q1"]), float(q["q2"]), True
    q1 = chi2_quantile_wilson_hilferty(df, 1.0 - alpha1)
    q2 = chi2_quantile_wilson_hilferty(df, 1.0 - alpha2)
    return q1, q2, False


def clamp(x: float, lo: float, hi: float) -> float:
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


class GlobalSimulationRunner:
    def __init__(
        self,
        cycles: int = 10000,
        mode: str = "nominal",
        seed: Optional[int] = None,
        allowed_dof: Tuple[int, ...] = DEFAULT_ALLOWED_DOF,
        print_every: int = 1000,
    ):
        self.cycles = cycles
        self.mode = mode.strip().lower()
        self.seed = seed
        self.allowed_dof = tuple(int(x) for x in allowed_dof if int(x) > 0)
        self.print_every = max(1, int(print_every))

        self.stats: Dict[str, int] = {
            "ACCEPTED": 0,
            "UNKNOWN": 0,
            "REJECTED": 0,
            "TOTAL_ANOMALIES": 0,
            "CRITICAL_FAILURES": 0,
            "INJECTED_SPOOF": 0,
            "INJECTED_DROPOUT": 0,
            "INJECTED_CORRELATED": 0,
            "INJECTED_TOTAL": 0,
            "INJECTED_DETECTED": 0,
            "INJECTED_REJECTED": 0,
            "INJECTED_MISSED": 0,
        }

        self.per_dof: Dict[int, Dict[str, int]] = {}
        for nu in self.allowed_dof:
            self.per_dof[nu] = {"ACCEPTED": 0, "UNKNOWN": 0, "REJECTED": 0, "TOTAL": 0}

        self.logs: List[str] = []

        self.mode_overrides = self._mode_overrides(self.mode)

    def _mode_overrides(self, mode: str) -> Dict[str, float]:
        if mode == "cruise":
            return {
                "q1_mult": 1.00,
                "q2_mult": 1.20,
                "unknown_weight": 0.30,
                "reject_penalty": 1.00,
                "critical_d2_factor": 3.00,
                "temp_alpha": 1.0,
                "t_min": 0.0,
                "t_max": 0.5,
            }
        if mode in ("precision", "dock", "landing"):
            return {
                "q1_mult": 0.85,
                "q2_mult": 0.95,
                "unknown_weight": 0.10,
                "reject_penalty": 1.25,
                "critical_d2_factor": 2.00,
                "temp_alpha": 1.0,
                "t_min": 0.0,
                "t_max": 0.5,
            }
        return {
            "q1_mult": 1.00,
            "q2_mult": 1.00,
            "unknown_weight": 0.20,
            "reject_penalty": 1.10,
            "critical_d2_factor": 2.50,
            "temp_alpha": 1.0,
            "t_min": 0.0,
            "t_max": 0.5,
        }

    def log(self, message: str):
        if len(self.logs) < 2000:
            self.logs.append(message)

    def _rand_truth_vector(self, nu: int) -> List[float]:
        return [random.uniform(10.0, 100.0) for _ in range(nu)]

    def _rand_sigmas(self, nu: int, noise_factor: float) -> Tuple[List[float], List[float]]:
        sigma_meas = [random.uniform(0.5, 2.0) * (noise_factor / 2.0) for _ in range(nu)]
        sigma_pred = [random.uniform(0.1, 0.5) for _ in range(nu)]
        return sigma_meas, sigma_pred

    def _make_prediction(self, truth: List[float], noise_factor: float) -> List[float]:
        return [t + random.gauss(0.0, 0.5 * noise_factor) for t in truth]

    def _make_measurement(self, truth: List[float], noise_factor: float) -> List[float]:
        return [t + random.gauss(0.0, 1.0 * noise_factor) for t in truth]

    def _inject_anomalies(
        self,
        prediction: List[float],
        measurement: List[float],
        sigma_meas: List[float],
        sigma_pred: List[float],
        noise_factor: float,
    ) -> Tuple[bool, str]:
        injected = False
        anomaly_type = "NONE"

        p_spoof = 0.020
        p_dropout = 0.010
        p_correlated = 0.010

        u = random.random()
        if u < p_spoof:
            injected = True
            anomaly_type = "SPOOF"
            self.stats["INJECTED_SPOOF"] += 1
            self.stats["INJECTED_TOTAL"] += 1

            dims = len(measurement)
            k = random.randint(1, max(1, dims // 2))
            idxs = random.sample(range(dims), k=k)

            for j in idxs:
                bias = random.uniform(5.0, 12.0) * math.hypot(sigma_meas[j], sigma_pred[j])
                measurement[j] += bias * (1.0 if random.random() < 0.5 else -1.0)

        elif u < p_spoof + p_dropout:
            injected = True
            anomaly_type = "DROPOUT"
            self.stats["INJECTED_DROPOUT"] += 1
            self.stats["INJECTED_TOTAL"] += 1

            dims = len(sigma_meas)
            j = random.randrange(dims)
            if random.random() < 0.5:
                sigma_meas[j] *= random.uniform(0.05, 0.25)
            else:
                sigma_meas[j] *= random.uniform(3.0, 10.0)

        elif u < p_spoof + p_dropout + p_correlated:
            injected = True
            anomaly_type = "CORRELATED"
            self.stats["INJECTED_CORRELATED"] += 1
            self.stats["INJECTED_TOTAL"] += 1

            dims = len(measurement)
            bias = random.uniform(3.0, 8.0) * (noise_factor / 2.0)
            sign = 1.0 if random.random() < 0.5 else -1.0
            for j in range(dims):
                measurement[j] += sign * bias

        return injected, anomaly_type

    def _compute_d2(self, prediction: List[float], measurement: List[float], sigma_meas: List[float], sigma_pred: List[float]) -> float:
        d2 = 0.0
        for p, m, sm, sp in zip(prediction, measurement, sigma_meas, sigma_pred):
            sigma_total = math.hypot(sm, sp)
            if not math.isfinite(sigma_total) or sigma_total <= 0.0:
                return float("inf")
            r = m - p
            d2 += (r / sigma_total) ** 2
        return d2

    def _gate(self, nu: int, d2: float) -> Tuple[str, float, float, bool]:
        q1, q2, is_precomputed = get_chi2_thresholds(nu, ALPHA_1, ALPHA_2)
        q1_eff = q1 * self.mode_overrides["q1_mult"]
        q2_eff = q2 * self.mode_overrides["q2_mult"]
        if d2 <= q1_eff:
            return "ACCEPTED", q1_eff, q2_eff, is_precomputed
        if d2 <= q2_eff:
            return "UNKNOWN", q1_eff, q2_eff, is_precomputed
        return "REJECTED", q1_eff, q2_eff, is_precomputed

    def _temperature(self, metric: float) -> float:
        alpha = float(self.mode_overrides["temp_alpha"])
        t_min = float(self.mode_overrides["t_min"])
        t_max = float(self.mode_overrides["t_max"])
        if not math.isfinite(metric):
            return 0.0
        temp = t_max * math.exp(-alpha * metric)
        return clamp(temp, t_min, t_max)

    def run(self):
        if self.seed is not None:
            random.seed(self.seed)

        print(f"{'='*88}")
        print(f" [!] STARTING PHYSICS-GATED STRESS TEST (ND Chi2): {self.cycles} CYCLES")
        print(f" [!] MODE: {self.mode.upper()} | DOF SET: {list(self.allowed_dof)}")
        print(f" [!] THRESHOLDS: PHI={PHI:.6f} | PI={PI:.6f}")
        print(f" [!] 1D COVERAGE: P(|Z|<=PHI)={P_COVER_PHI_1D:.4f} -> a1={ALPHA_1:.4f} | P(|Z|<=PI)={P_COVER_PI_1D:.4f} -> a2={ALPHA_2:.4f}")
        print(f"{'='*88}\n")

        print(" [i] PRECOMPUTED Chi2 QUANTILES (q1=chi2_{{1-a1}}(nu), q2=chi2_{{1-a2}}(nu))")
        print("     (Values used when nu is in the precomputed table; otherwise Wilson-Hilferty approximation)")
        print("     | nu |    q1(~phi-equiv) |    q2(~pi-equiv) |")
        print("     |---:|---------------:|---------------:|")
        for nu in sorted(set(self.allowed_dof)):
            q1, q2, pre = get_chi2_thresholds(nu, ALPHA_1, ALPHA_2)
            if pre:
                print(f"     | {nu:2d} | {q1:14.4f} | {q2:14.4f} |")
            else:
                print(f"     | {nu:2d} | {q1:14.4f} | {q2:14.4f} |*")
        print("     * approximated (not precomputed)\n")

        print(" [i] MODE OVERRIDES")
        print(f"     q1_mult={self.mode_overrides['q1_mult']:.2f} | q2_mult={self.mode_overrides['q2_mult']:.2f} | t_min={self.mode_overrides['t_min']:.2f} | t_max={self.mode_overrides['t_max']:.2f} | temp_alpha={self.mode_overrides['temp_alpha']:.2f}")
        if self.mode == "cruise":
            print(f"     example override: reject boundary widened (~pi*1.2 concept) via q2_mult={self.mode_overrides['q2_mult']:.2f}")
        if self.mode in ("precision", "dock", "landing"):
            print(f"     example override: trust boundary tightened (~phi*0.85 concept) via q1_mult={self.mode_overrides['q1_mult']:.2f}")
        print("")

        for i in range(1, self.cycles + 1):
            nu = random.choice(self.allowed_dof)
            self.per_dof[nu]["TOTAL"] += 1

            noise_factor = random.uniform(0.1, 5.0)

            truth = self._rand_truth_vector(nu)
            prediction = self._make_prediction(truth, noise_factor)
            measurement = self._make_measurement(truth, noise_factor)
            sigma_meas, sigma_pred = self._rand_sigmas(nu, noise_factor)

            injected, anomaly_type = self._inject_anomalies(prediction, measurement, sigma_meas, sigma_pred, noise_factor)

            d2 = self._compute_d2(prediction, measurement, sigma_meas, sigma_pred)
            status, q1_eff, q2_eff, is_precomputed = self._gate(nu, d2)

            if status == "ACCEPTED":
                self.stats["ACCEPTED"] += 1
                self.per_dof[nu]["ACCEPTED"] += 1
            elif status == "UNKNOWN":
                self.stats["UNKNOWN"] += 1
                self.per_dof[nu]["UNKNOWN"] += 1
                self.stats["TOTAL_ANOMALIES"] += 1
            else:
                self.stats["REJECTED"] += 1
                self.per_dof[nu]["REJECTED"] += 1
                self.stats["TOTAL_ANOMALIES"] += 1

            if status != "ACCEPTED":
                temp = self._temperature(math.sqrt(d2) if math.isfinite(d2) else float("inf"))
                _ = temp

            if injected:
                if status != "ACCEPTED":
                    self.stats["INJECTED_DETECTED"] += 1
                else:
                    self.stats["INJECTED_MISSED"] += 1
                if status == "REJECTED":
                    self.stats["INJECTED_REJECTED"] += 1

            critical_threshold = q2_eff * float(self.mode_overrides["critical_d2_factor"])
            if math.isfinite(d2) and d2 > critical_threshold:
                self.stats["CRITICAL_FAILURES"] += 1

            if i == 1 or i % self.print_every == 0:
                d2_s = f"{d2:9.3f}" if math.isfinite(d2) else "      inf"
                pre_tag = "PRE" if is_precomputed else "APP"
                inj_tag = anomaly_type if injected else "NONE"
                print(
                    f"Cycle {i:5d}: nu={nu:2d} | d^2={d2_s} | q1={q1_eff:7.3f} | q2={q2_eff:7.3f} | {pre_tag} | INJ={inj_tag:10s} | {status}"
                )

        self.print_summary()

    def print_summary(self):
        print(f"\n{'='*88}")
        print(f" [!] STRESS TEST SUMMARY ({self.cycles} CYCLES) | MODE={self.mode.upper()}")
        print(f"{'='*88}")

        acc = self.stats["ACCEPTED"]
        unk = self.stats["UNKNOWN"]
        rej = self.stats["REJECTED"]

        print(f"  ACCEPTED:   {acc:6d} ({(acc/self.cycles)*100:6.2f}%)")
        print(f"  UNKNOWN:    {unk:6d} ({(unk/self.cycles)*100:6.2f}%)")
        print(f"  REJECTED:   {rej:6d} ({(rej/self.cycles)*100:6.2f}%)")
        print("-" * 60)
        print(f"  TOTAL ANOMALIES (UNKNOWN+REJECT): {self.stats['TOTAL_ANOMALIES']:6d}")
        print(f"  CRITICAL FAILURES:                {self.stats['CRITICAL_FAILURES']:6d}")
        print("-" * 60)

        injected_total = self.stats["INJECTED_TOTAL"]
        if injected_total > 0:
            detected = self.stats["INJECTED_DETECTED"]
            rejected = self.stats["INJECTED_REJECTED"]
            missed = self.stats["INJECTED_MISSED"]
            print("  INJECTED ANOMALIES (GROUND-TRUTH)")
            print(f"    TOTAL:     {injected_total:6d}")
            print(f"    SPOOF:     {self.stats['INJECTED_SPOOF']:6d}")
            print(f"    DROPOUT:   {self.stats['INJECTED_DROPOUT']:6d}")
            print(f"    CORRELATED:{self.stats['INJECTED_CORRELATED']:6d}")
            print("  DETECTION")
            print(f"    DETECTED (UNKNOWN/REJECT): {detected:6d} ({(detected/injected_total)*100:6.2f}%)")
            print(f"    REJECTED (hard stop):      {rejected:6d} ({(rejected/injected_total)*100:6.2f}%)")
            print(f"    MISSED (ACCEPTED):         {missed:6d} ({(missed/injected_total)*100:6.2f}%)")
            print("-" * 60)

        print("  PER-DOF BREAKDOWN")
        print("  | nu |   total | accepted | unknown | rejected | accept% | unknown% | reject% |")
        print("  |---:|--------:|---------:|--------:|---------:|--------:|---------:|--------:|")
        for nu in sorted(self.per_dof.keys()):
            t = self.per_dof[nu]["TOTAL"]
            if t <= 0:
                continue
            a = self.per_dof[nu]["ACCEPTED"]
            u = self.per_dof[nu]["UNKNOWN"]
            r = self.per_dof[nu]["REJECTED"]
            print(
                f"  | {nu:2d} | {t:6d} | {a:7d} | {u:7d} | {r:7d} | {a/t*100:7.2f} | {u/t*100:7.2f} | {r/t*100:7.2f} |"
            )
        print("-" * 60)

        unknown_weight = float(self.mode_overrides["unknown_weight"])
        reject_penalty = float(self.mode_overrides["reject_penalty"])
        health = (acc + unknown_weight * unk - reject_penalty * rej) / self.cycles
        health_pct = 100.0 * clamp(health, 0.0, 1.0)

        print(f"  HEALTH SCORE: {health_pct:6.2f}%")
        if health_pct >= 90.0:
            print("  STATUS: [STABLE] - Gate behavior in expected envelope.")
        elif health_pct >= 70.0:
            print("  STATUS: [DEGRADED] - Noise/drift elevated; calibration recommended.")
        else:
            print("  STATUS: [UNSTABLE] - Frequent rejects/anomalies; investigate sensors/model.")
        print(f"{'='*88}\n")


def parse_args(argv: List[str]) -> Dict[str, object]:
    args: Dict[str, object] = {
        "cycles": 10000,
        "mode": "nominal",
        "seed": None,
        "allowed_dof": DEFAULT_ALLOWED_DOF,
        "print_every": 1000,
    }

    if len(argv) >= 2:
        args["cycles"] = int(argv[1])

    if len(argv) >= 3:
        args["mode"] = str(argv[2]).strip().lower()

    if len(argv) >= 4:
        s = argv[3].strip().lower()
        args["seed"] = None if s in ("none", "null", "") else int(s)

    if len(argv) >= 5:
        dof_str = argv[4].strip()
        if dof_str:
            parts = [p.strip() for p in dof_str.split(",") if p.strip()]
            dofs = tuple(int(p) for p in parts)
            args["allowed_dof"] = dofs

    if len(argv) >= 6:
        args["print_every"] = int(argv[5])

    return args


if __name__ == "__main__":
    cfg = parse_args(sys.argv)
    runner = GlobalSimulationRunner(
        cycles=int(cfg["cycles"]),
        mode=str(cfg["mode"]),
        seed=None if cfg["seed"] is None else int(cfg["seed"]),
        allowed_dof=tuple(cfg["allowed_dof"]),
        print_every=int(cfg["print_every"]),
    )
    runner.run()
