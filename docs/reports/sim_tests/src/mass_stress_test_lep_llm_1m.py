# Copyright (c) 2024-2026 BorodinD&V
# simulations/mass_stress_test_lep_llm_1m.py
# MASSIVE STRESS TEST: LEP Inductive Charging + Wire-Perch Geometry + Physics-Gated LLM Policy

import argparse
import math
import random
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


# ==============================================================================
# 0) CANONICAL CONSTANTS (Physics-Gated Grounding)
# ==============================================================================

PHI = (1.0 + math.sqrt(5.0)) / 2.0  # 1.618...
PI = math.pi                        # 3.14159...

# 1D coverages for Z~N(0,1), two-sided
P_COVER_PHI_1D = 0.8943
P_COVER_PI_1D = 0.9983
ALPHA_1 = 1.0 - P_COVER_PHI_1D  # 0.1057
ALPHA_2 = 1.0 - P_COVER_PI_1D   # 0.0017


# ==============================================================================
# 1) MATH HELPERS (Robust, stdlib-only)
# ==============================================================================

def clamp(x: float, lo: float, hi: float) -> float:
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def safe_hypot(a: float, b: float, eps: float = 1e-9) -> float:
    v = math.hypot(a, b)
    return v if v > eps else eps


def normal_inv_cdf(p: float) -> float:
    return statistics.NormalDist().inv_cdf(p)


def chi2_quantile_wilson_hilferty(df: int, p: float) -> float:
    if df <= 0:
        return float("inf")
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return float("inf")
    z = normal_inv_cdf(p)
    a = 2.0 / (9.0 * df)
    t = 1.0 - a + z * math.sqrt(a)
    return df * (t ** 3) if t > 0.0 else 0.0


def chi2_thresholds(df: int) -> Tuple[float, float]:
    q1 = chi2_quantile_wilson_hilferty(df, 1.0 - ALPHA_1)
    q2 = chi2_quantile_wilson_hilferty(df, 1.0 - ALPHA_2)
    return q1, q2


# ==============================================================================
# 2) PHYSICS GATES
# ==============================================================================

@dataclass
class GateDecision:
    zone: str        # "ACCEPTED" | "UNKNOWN" | "REJECTED"
    metric: float    # z (1D) or d2 (ND)
    sigma_total: float


class ZGate1D:
    def __init__(self, z_ok: float = PHI, z_max: float = PI):
        self.z_ok = z_ok
        self.z_max = z_max

    def check(self, pred: float, meas: float, sigma_meas: float, sigma_pred: float) -> GateDecision:
        sigma_total = safe_hypot(sigma_meas, sigma_pred)
        z = abs(meas - pred) / sigma_total
        if z <= self.z_ok:
            return GateDecision("ACCEPTED", z, sigma_total)
        if z <= self.z_max:
            return GateDecision("UNKNOWN", z, sigma_total)
        return GateDecision("REJECTED", z, sigma_total)


class Chi2GateND:
    def __init__(self, df: int, q1_scale: float = 1.0, q2_scale: float = 1.0):
        self.df = df
        q1, q2 = chi2_thresholds(df)
        self.q1 = q1 * q1_scale
        self.q2 = q2 * q2_scale

    def check_diag_cov(self, pred: List[float], meas: List[float], sigma_meas: List[float], sigma_pred: List[float]) -> GateDecision:
        d2 = 0.0
        sigma_total_last = 0.0
        for p, m, sm, sp in zip(pred, meas, sigma_meas, sigma_pred):
            s_total = safe_hypot(sm, sp)
            sigma_total_last = s_total
            r = (m - p) / s_total
            d2 += r * r

        if d2 <= self.q1:
            return GateDecision("ACCEPTED", d2, sigma_total_last)
        if d2 <= self.q2:
            return GateDecision("UNKNOWN", d2, sigma_total_last)
        return GateDecision("REJECTED", d2, sigma_total_last)


# ==============================================================================
# 3) SENSOR MODELS (Wire-perch environment)
# ==============================================================================

@dataclass
class SensorSample1D:
    value: float
    sigma: float
    is_spoof: bool


class CameraY:
    def __init__(self, sigma_base_m: float = 0.001, sigma_per_m: float = 0.002, outlier_p: float = 0.0008):
        self.sigma_base_m = sigma_base_m
        self.sigma_per_m = sigma_per_m
        self.outlier_p = outlier_p

    def measure(self, y_true: float, z_true: float) -> SensorSample1D:
        dist = math.hypot(y_true, z_true)
        sigma = self.sigma_base_m + self.sigma_per_m * dist
        noise = random.gauss(0.0, sigma)
        if random.random() < self.outlier_p:
            noise += random.uniform(-0.15, 0.15)
            return SensorSample1D(y_true + noise, sigma * 3.0, True)
        return SensorSample1D(y_true + noise, sigma, False)


class MagY:
    def __init__(
        self,
        sigma_base_m: float = 0.10,
        emi_k: float = 0.50,
        spoof_p_near: float = 0.05,
        near_r_m: float = 0.20,
        spoof_jump_m: float = 2.0,
        saturate_p_near: float = 0.20,
    ):
        self.sigma_base_m = sigma_base_m
        self.emi_k = emi_k
        self.spoof_p_near = spoof_p_near
        self.near_r_m = near_r_m
        self.spoof_jump_m = spoof_jump_m
        self.saturate_p_near = saturate_p_near

    def measure(self, y_true: float, z_true: float) -> SensorSample1D:
        r = math.hypot(y_true, z_true)
        r_eff = r if r > 0.05 else 0.05
        sigma_emi = self.emi_k / r_eff
        sigma = self.sigma_base_m + sigma_emi

        noise = random.gauss(0.0, sigma)
        is_spoof = False

        if r <= self.near_r_m and random.random() < self.saturate_p_near:
            noise += random.uniform(-0.8, 0.8)
            is_spoof = True

        if r <= self.near_r_m and random.random() < self.spoof_p_near:
            noise += random.uniform(-self.spoof_jump_m, self.spoof_jump_m)
            is_spoof = True

        return SensorSample1D(y_true + noise, sigma, is_spoof)


# ==============================================================================
# 4) LEP INDUCTIVE CHARGING MODEL (Abstracted; geometry-driven)
# ==============================================================================

@dataclass
class ChargeStep:
    p_w: float
    dv_batt: float
    dtemp_c: float


class InductiveHarvester:
    def __init__(
        self,
        line_freq_hz: float = 50.0,
        line_current_rms_a: float = 450.0,
        m0_h: float = 2.5e-6,
        gap_scale_m: float = 0.03,
        eta: float = 0.55,
        r_load_ohm: float = 8.0,
        p_cap_w: float = 180.0,
        thermal_tau_s: float = 35.0,
        core_loss_k: float = 0.010,
    ):
        self.omega = 2.0 * math.pi * line_freq_hz
        self.i_rms = line_current_rms_a
        self.m0 = m0_h
        self.g0 = gap_scale_m
        self.eta = eta
        self.r_load = r_load_ohm
        self.p_cap = p_cap_w
        self.thermal_tau = thermal_tau_s
        self.core_loss_k = core_loss_k

    def coupling(self, gap_m: float, align: float) -> float:
        g = gap_m if gap_m > 0.0 else 0.0
        a = clamp(align, 0.0, 1.0)
        return math.exp(-g / self.g0) * a

    def step(self, gap_m: float, align: float, temp_c: float, dt_s: float) -> ChargeStep:
        k = self.coupling(gap_m, align)
        m = self.m0 * k

        v_rms = self.omega * m * self.i_rms
        p_raw = (v_rms * v_rms) / max(self.r_load, 1e-6)
        p = clamp(self.eta * p_raw, 0.0, self.p_cap)

        # Battery delta is abstracted: 1.0 unit == 1% battery per 60 Wh pack
        # Convert W*dt to "battery %" with a configurable scaling
        wh = (p * dt_s) / 3600.0
        dv = wh / 0.60  # 60 Wh pack -> 1.0 == 100%, so /0.60 => % points

        # Thermal: heating from harvested power + core losses, cooling to ambient(25C)
        ambient = 25.0
        core_loss = self.core_loss_k * (k * k) * (self.i_rms / 450.0) ** 2 * 100.0
        heat_in = (0.08 * p) + core_loss
        cool = (temp_c - ambient) / max(self.thermal_tau, 1e-6)
        dtemp = (heat_in * 0.02 - cool) * dt_s

        return ChargeStep(p, dv, dtemp)


# ==============================================================================
# 5) LLM POLICY EMULATION (Entropy Starvation)
# ==============================================================================

@dataclass
class LLMPolicyEvent:
    temp: float
    action: str


class LLMPolicy:
    def __init__(self, t_min: float = 0.0, t_max: float = 0.5, alpha: float = 1.0):
        self.t_min = t_min
        self.t_max = t_max
        self.alpha = alpha

    def decide(self, zone: str, metric: float) -> LLMPolicyEvent:
        if zone == "ACCEPTED":
            return LLMPolicyEvent(0.0, "SLEEP_FASTPATH")
        if zone == "REJECTED":
            return LLMPolicyEvent(0.0, "SAFE_MODE_BLOCK_AND_LOG")

        m = max(metric, 0.0)
        temp = clamp(self.t_max * math.exp(-self.alpha * m), self.t_min, self.t_max)
        return LLMPolicyEvent(temp, "ASK_CLARIFY_AND_REQUEST_EVIDENCE")


# ==============================================================================
# 6) EPISODE SIMULATION (Approach -> Perch -> Charge -> Depart)
# ==============================================================================

@dataclass
class EpisodeResult:
    success: bool
    spoof_injected: bool
    spoof_detected: bool
    final_y_m: float
    final_z_m: float
    charge_gain_pct: float
    max_temp_c: float


class LEPWireEpisode:
    def __init__(
        self,
        mode: str,
        y_tol_mm: float,
        z_contact_m: float,
        dt_s: float,
        approach_time_s: float,
        charge_time_s: float,
        sigma_pred_m: float,
        mag_sigma_scale: float,
        cam_sigma_scale: float,
    ):
        self.mode = mode
        self.y_tol_m = y_tol_mm / 1000.0
        self.z_contact_m = z_contact_m
        self.dt = dt_s
        self.steps_approach = max(1, int(approach_time_s / dt_s))
        self.steps_charge = max(1, int(charge_time_s / dt_s))
        self.sigma_pred = sigma_pred_m

        # Sensors
        self.cam = CameraY()
        self.mag = MagY()
        self.mag_sigma_scale = mag_sigma_scale
        self.cam_sigma_scale = cam_sigma_scale

        # Gates
        self.gate_cam = ZGate1D()
        self.gate_mag = ZGate1D()

        # Harvester + policy
        self.harvester = InductiveHarvester()
        self.llm = LLMPolicy()

        # Mode knobs
        if mode == "CRUISE":
            self.kp_y = 0.8
            self.kp_z = 0.7
            self.vz_fast = -0.7
            self.vz_slow = -0.2
        elif mode == "PRECISION":
            self.kp_y = 1.6
            self.kp_z = 1.2
            self.vz_fast = -0.35
            self.vz_slow = -0.08
        else:
            self.kp_y = 1.2
            self.kp_z = 0.9
            self.vz_fast = -0.5
            self.vz_slow = -0.1

    def run(self) -> EpisodeResult:
        y = random.gauss(0.50, 0.20)  # lateral offset (m)
        z = random.gauss(5.00, 0.80)  # altitude (m)
        vy = 0.0
        vz = 0.0

        battery = random.uniform(15.0, 30.0)
        temp = random.uniform(20.0, 35.0)
        max_temp = temp

        spoof_injected = False
        spoof_detected = False

        est_y = y
        est_z = z

        # Approach dynamics
        for _ in range(self.steps_approach):
            wind_y = random.gauss(0.0, 0.25) + 0.8 * math.sin(random.random() * 2.0 * math.pi)

            # Prediction (dead-reckoning)
            pred_y = est_y + vy * self.dt
            pred_z = est_z + vz * self.dt

            # Measurements
            cam_s = self.cam.measure(y, z)
            mag_s = self.mag.measure(y, z)
            spoof_injected = spoof_injected or cam_s.is_spoof or mag_s.is_spoof

            cam_sigma = cam_s.sigma * self.cam_sigma_scale
            mag_sigma = mag_s.sigma * self.mag_sigma_scale

            d_cam = self.gate_cam.check(pred_y, cam_s.value, cam_sigma, self.sigma_pred)
            d_mag = self.gate_mag.check(pred_y, mag_s.value, mag_sigma, self.sigma_pred)

            # Policy / spoof detection signal
            if d_cam.zone == "REJECTED" and cam_s.is_spoof:
                spoof_detected = True
            if d_mag.zone == "REJECTED" and mag_s.is_spoof:
                spoof_detected = True

            # Fusion choice: Camera > Mag > Prediction
            used_zone = "UNKNOWN"
            used_metric = 0.0

            if d_cam.zone == "ACCEPTED":
                est_y = cam_s.value
                used_zone = d_cam.zone
                used_metric = d_cam.metric
            elif d_mag.zone == "ACCEPTED":
                est_y = mag_s.value
                used_zone = d_mag.zone
                used_metric = d_mag.metric
            else:
                est_y = pred_y
                used_zone = "UNKNOWN"
                used_metric = min(d_cam.metric, d_mag.metric)

            # LLM policy event (emulated)
            _ = self.llm.decide(used_zone, used_metric)

            # Control: reduce lateral and descend
            err_y = -est_y
            ay_cmd = self.kp_y * err_y + wind_y
            vy += ay_cmd * self.dt
            y += vy * self.dt

            target_vz = self.vz_fast if z > 1.0 else self.vz_slow
            if z <= 0.08:
                target_vz = 0.0
            err_vz = target_vz - vz
            az_cmd = self.kp_z * err_vz
            vz += az_cmd * self.dt
            z += vz * self.dt

            est_z = z

            if z <= self.z_contact_m:
                break

        # If not reached contact, fail early
        if z > self.z_contact_m + 0.05:
            return EpisodeResult(
                success=False,
                spoof_injected=spoof_injected,
                spoof_detected=spoof_detected,
                final_y_m=y,
                final_z_m=z,
                charge_gain_pct=0.0,
                max_temp_c=max_temp,
            )

        # Charging phase: gap/align from final geometry
        for _ in range(self.steps_charge):
            gap = max(0.0, abs(y)) + max(0.0, z)  # abstracted mechanical separation
            align = clamp(1.0 - (abs(y) / 0.15), 0.0, 1.0)

            ch = self.harvester.step(gap_m=gap, align=align, temp_c=temp, dt_s=self.dt)
            battery = clamp(battery + ch.dv_batt, 0.0, 100.0)
            temp += ch.dtemp_c
            max_temp = max(max_temp, temp)

            # If overheating, safe detach
            if temp >= 85.0:
                break

        # Success criterion: mm-level perch and no overheat
        ok_y = abs(y) <= self.y_tol_m
        ok_temp = max_temp < 95.0
        success = ok_y and ok_temp

        return EpisodeResult(
            success=success,
            spoof_injected=spoof_injected,
            spoof_detected=spoof_detected,
            final_y_m=y,
            final_z_m=z,
            charge_gain_pct=max(0.0, battery - 20.0),
            max_temp_c=max_temp,
        )


# ==============================================================================
# 7) AUTO-CALIBRATION (Online sigma scaling via empirical quantiles)
# ==============================================================================

class AutoCalibrator:
    def __init__(self, target_z_hi: float = PI, p_hi: float = P_COVER_PI_1D):
        self.target_z_hi = target_z_hi
        self.p_hi = p_hi
        self.samples: List[float] = []

    def add_z(self, z: float):
        if math.isfinite(z):
            self.samples.append(abs(z))

    def recommended_sigma_scale(self) -> float:
        if len(self.samples) < 200:
            return 1.0
        xs = sorted(self.samples)
        idx = int(clamp(self.p_hi, 0.0, 1.0) * (len(xs) - 1))
        z_q = xs[idx]
        if z_q <= 1e-9:
            return 1.0
        return z_q / self.target_z_hi


# ==============================================================================
# 8) MASS RUNNER
# ==============================================================================

@dataclass
class RunStats:
    episodes: int = 0
    success: int = 0
    spoof_injected: int = 0
    spoof_detected: int = 0
    spoof_missed: int = 0
    overheat: int = 0

    y_abs_sum: float = 0.0
    y_abs_max: float = 0.0
    temp_max_sum: float = 0.0
    temp_max_max: float = 0.0
    charge_gain_sum: float = 0.0

    def update(self, r: EpisodeResult):
        self.episodes += 1
        if r.success:
            self.success += 1
        if r.spoof_injected:
            self.spoof_injected += 1
            if r.spoof_detected:
                self.spoof_detected += 1
            else:
                self.spoof_missed += 1

        if r.max_temp_c >= 95.0:
            self.overheat += 1

        y_abs = abs(r.final_y_m)
        self.y_abs_sum += y_abs
        self.y_abs_max = max(self.y_abs_max, y_abs)

        self.temp_max_sum += r.max_temp_c
        self.temp_max_max = max(self.temp_max_max, r.max_temp_c)

        self.charge_gain_sum += r.charge_gain_pct


def run_mass(
    episodes: int,
    mode: str,
    seed: int,
    y_tol_mm: float,
    autocal_warmup: int,
    log_dir: Path,
    print_every: int,
) -> int:
    random.seed(seed)

    dt = 0.05
    approach_time = 12.0 if mode == "PRECISION" else 8.0
    charge_time = 20.0 if mode == "CRUISE" else 14.0
    sigma_pred = 0.05

    mag_sigma_scale = 1.0
    cam_sigma_scale = 1.0

    cam_cal = AutoCalibrator()
    mag_cal = AutoCalibrator()

    stats = RunStats()
    t0 = time.time()

    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"mass_lep_{mode.lower()}_{episodes}_seed{seed}.log"

    with log_path.open("w", encoding="utf-8") as f:
        f.write("MASS LEP + WIRE PERCH SIM\n")
        f.write(f"episodes={episodes} mode={mode} seed={seed}\n")
        f.write(f"y_tol_mm={y_tol_mm}\n")
        f.write(f"autocal_warmup={autocal_warmup}\n")

        for i in range(1, episodes + 1):
            ep = LEPWireEpisode(
                mode=mode,
                y_tol_mm=y_tol_mm,
                z_contact_m=0.01,
                dt_s=dt,
                approach_time_s=approach_time,
                charge_time_s=charge_time,
                sigma_pred_m=sigma_pred,
                mag_sigma_scale=mag_sigma_scale,
                cam_sigma_scale=cam_sigma_scale,
            )

            r = ep.run()
            stats.update(r)

            # Warmup autocal: estimate sigma scaling using empirical z quantiles (clean-ish)
            # Use internal gate metrics from a proxy: derive pseudo-z from final error vs tolerance band
            if i <= autocal_warmup:
                z_cam_proxy = abs(r.final_y_m) / safe_hypot(0.01, sigma_pred)
                z_mag_proxy = abs(r.final_y_m) / safe_hypot(0.10, sigma_pred)
                cam_cal.add_z(z_cam_proxy)
                mag_cal.add_z(z_mag_proxy)

                if i == autocal_warmup:
                    cam_scale = cam_cal.recommended_sigma_scale()
                    mag_scale = mag_cal.recommended_sigma_scale()
                    cam_sigma_scale = clamp(cam_sigma_scale * cam_scale, 0.5, 6.0)
                    mag_sigma_scale = clamp(mag_sigma_scale * mag_scale, 0.5, 12.0)
                    f.write(f"autocal_cam_sigma_scale={cam_sigma_scale:.4f}\n")
                    f.write(f"autocal_mag_sigma_scale={mag_sigma_scale:.4f}\n")

            if print_every > 0 and (i % print_every == 0 or i == 1):
                succ = 100.0 * stats.success / stats.episodes
                inj = stats.spoof_injected
                det = stats.spoof_detected
                det_rate = (100.0 * det / inj) if inj > 0 else 0.0
                avg_y_mm = (stats.y_abs_sum / stats.episodes) * 1000.0
                print(
                    f"ep {i:>8}/{episodes} | success={succ:6.2f}% | spoof det={det_rate:6.2f}% "
                    f"| avg|y|={avg_y_mm:7.2f}mm | maxT={stats.temp_max_max:6.1f}C "
                    f"| sigma(cam,mag)=({cam_sigma_scale:4.2f},{mag_sigma_scale:4.2f})"
                )

            if i % 2000 == 0:
                f.write(
                    f"ep={i} success={stats.success} spoof_inj={stats.spoof_injected} "
                    f"spoof_det={stats.spoof_detected} spoof_miss={stats.spoof_missed} "
                    f"overheat={stats.overheat}\n"
                )

        t1 = time.time()
        dt_run = max(t1 - t0, 1e-9)

        succ = 100.0 * stats.success / stats.episodes
        inj = stats.spoof_injected
        det = stats.spoof_detected
        miss = stats.spoof_missed
        det_rate = (100.0 * det / inj) if inj > 0 else 0.0
        miss_rate = (100.0 * miss / inj) if inj > 0 else 0.0

        avg_y_mm = (stats.y_abs_sum / stats.episodes) * 1000.0
        max_y_mm = stats.y_abs_max * 1000.0
        avg_temp = stats.temp_max_sum / stats.episodes
        avg_charge = stats.charge_gain_sum / stats.episodes

        f.write("SUMMARY\n")
        f.write(f"runtime_s={dt_run:.3f}\n")
        f.write(f"eps_per_s={(stats.episodes/dt_run):.2f}\n")
        f.write(f"success_pct={succ:.4f}\n")
        f.write(f"spoof_injected={inj}\n")
        f.write(f"spoof_detected={det}\n")
        f.write(f"spoof_missed={miss}\n")
        f.write(f"spoof_detection_rate_pct={det_rate:.4f}\n")
        f.write(f"spoof_miss_rate_pct={miss_rate:.4f}\n")
        f.write(f"avg_abs_y_mm={avg_y_mm:.4f}\n")
        f.write(f"max_abs_y_mm={max_y_mm:.4f}\n")
        f.write(f"avg_max_temp_c={avg_temp:.4f}\n")
        f.write(f"max_temp_c={stats.temp_max_max:.4f}\n")
        f.write(f"avg_charge_gain_pct={avg_charge:.4f}\n")
        f.write(f"overheat_events={stats.overheat}\n")
        f.write(f"final_sigma_scales cam={cam_sigma_scale:.4f} mag={mag_sigma_scale:.4f}\n")

    print(f"saved: {log_path}")
    return 0


# ==============================================================================
# 9) CLI
# ==============================================================================

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--episodes", type=int, default=1_000_000)
    p.add_argument("--mode", type=str, default="DEFAULT", choices=["DEFAULT", "CRUISE", "PRECISION"])
    p.add_argument("--seed", type=int, default=12345)
    p.add_argument("--y_tol_mm", type=float, default=10.0)
    p.add_argument("--autocal_warmup", type=int, default=50_000)
    p.add_argument("--log_dir", type=str, default="sim_tests/logs")
    p.add_argument("--print_every", type=int, default=100_000)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    sys_exit = run_mass(
        episodes=args.episodes,
        mode=args.mode,
        seed=args.seed,
        y_tol_mm=args.y_tol_mm,
        autocal_warmup=args.autocal_warmup,
        log_dir=Path(args.log_dir),
        print_every=args.print_every,
    )
    raise SystemExit(sys_exit)
