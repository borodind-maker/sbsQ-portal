import random
import math

# --- Constants ---
PHI = 0.6180339887
PI = 3.1415926535
THRESH_VERIFIED = PHI  # Z-score limit for perfect trust
THRESH_REJECT = PI     # Z-score limit for hard reject

# --- Models ---

class VisualCoreSimulator:
    """Simulates LLaVA-Phi3 output based on ground truth + noise"""
    def __init__(self):
        self.objects = ["TANK", "APC", "TRUCK", "SOLDIER", "TREE", "ROCK", "NONE"]
        
    def dream(self, scenario_type):
        # Determine what the visual core 'thinks' it sees
        if scenario_type == "CLEAR_DAY":
            obj = random.choice(["TANK", "TRUCK", "APC"])
            conf = random.uniform(0.85, 0.99)
        elif scenario_type == "FOGGY":
            obj = random.choice(["ROCK", "TREE", "SOLDIER"])
            conf = random.uniform(0.40, 0.70)
        elif scenario_type == "NIGHT_VISION":
            obj = random.choice(["TANK", "NONE"])
            conf = random.uniform(0.60, 0.90)
        elif scenario_type == "HALLUCINATION_TRIGGER":
            obj = "TANK" # Imagining a tank where there is none
            conf = random.uniform(0.90, 0.99) # Very confident (Dunning-Kruger effect of AI)
        else:
            obj = "NONE"
            conf = 0.1
            
        return {"object": obj, "confidence": conf}

class TelemetrySimulator:
    """Generates physical context for the dream"""
    def get_context(self, scenario_type):
        ctx = {}
        if scenario_type == "CLEAR_DAY":
            ctx["light_lux"] = random.randint(1000, 5000)
            ctx["altitude"] = random.uniform(30, 100)
            ctx["speed"] = random.uniform(10, 40) # km/h
            ctx["magnetic_anomaly"] = random.choice([True, False]) # 50/50 chance for true metal
            ctx["sensor_sigma"] = 0.5 # Normal
        elif scenario_type == "FOGGY":
            ctx["light_lux"] = random.randint(200, 500)
            ctx["altitude"] = random.uniform(10, 30)
            ctx["speed"] = random.uniform(5, 15)
            ctx["magnetic_anomaly"] = False
            ctx["sensor_sigma"] = 1.5 # High uncertainty
        elif scenario_type == "NIGHT_VISION":
            ctx["light_lux"] = random.randint(0, 5) # Pitch black
            ctx["altitude"] = random.uniform(30, 50)
            ctx["speed"] = random.uniform(20, 30)
            ctx["magnetic_anomaly"] = True # Thermal/Magnetic targeting
            ctx["sensor_sigma"] = 0.8
        elif scenario_type == "HALLUCINATION_TRIGGER":
            # Context that SHOULD contradict a visual hit
            ctx["light_lux"] = random.randint(0, 10) # Too dark for normal cam
            ctx["altitude"] = 500 # Too high to see detail
            ctx["speed"] = 120 # Too fast (blur)
            ctx["magnetic_anomaly"] = False # No metal
            ctx["sensor_sigma"] = 0.5
            
        return ctx

class NeuralLogicCore:
    """Gemini Nano Simulator - The Auditor"""
    def audit(self, visual_claim, telemetry):
        reasons = []
        score = 0
        
        # 1. Light Check
        if telemetry["light_lux"] < 10 and not visual_claim["object"] == "NONE":
            # If it's dark, Visual Core shouldn't see normal things unless thermal (assuming no thermal flag here for simplicity)
            reasons.append("TOO_DARK")
            score -= 10
        else:
            score += 1
            
        # 2. Speed/Blur Check
        if telemetry["speed"] > 80 and visual_claim["confidence"] > 0.9:
            reasons.append("SPEED_BLUR_RISK")
            score -= 5
        
        # 3. Magnetic Confirmation (The Physics Gate)
        if visual_claim["object"] in ["TANK", "APC", "TRUCK"]:
            if telemetry["magnetic_anomaly"]:
                reasons.append("MAGNETIC_CONFIRM")
                score += 5
            else:
                reasons.append("NO_MAGNETIC_SIG")
                score -= 2 # Not a hard reject, maybe plastic/composite, but suspicious
                
        # 4. Phi/Pi Z-Score Simulation (Simplified)
        # We simulate the Z-score calculation based on scenario consistency
        if "TOO_DARK" in reasons or "SPEED_BLUR_RISK" in reasons:
            z_score = random.uniform(3.2, 5.0) # > PI (Reject)
        elif "MAGNETIC_CONFIRM" in reasons:
            z_score = random.uniform(0.0, 0.6) # < PHI (Verified)
        else:
            z_score = random.uniform(0.7, 3.0) # Grey zone
            
        return {"audit_score": score, "z_score": z_score, "reasons": reasons}

# --- Main Simulation Loop ---

def run_bicameral_simulation():
    vis = VisualCoreSimulator()
    tel = TelemetrySimulator()
    logic = NeuralLogicCore()
    
    scenarios = (["CLEAR_DAY"] * 2000) + (["FOGGY"] * 1000) + (["NIGHT_VISION"] * 1000) + (["HALLUCINATION_TRIGGER"] * 1000)
    random.shuffle(scenarios)
    
    results = []
    total_cycles = len(scenarios)
    
    print(f"{'#'*100}")
    print(f"BICAMERAL DREAM SIMULATION ({total_cycles} CYCLES) - AUDIT VAL-02")
    print(f"Harmony Thresholds: PHI={PHI:.3f} | PI={PI:.3f}")
    print(f"{'#'*100}\n")
    
    headers = ["ID", "Scenario", "Visual (Phi-3)", "Conf", "Logic (Gemini)", "Z-Score", "Gate", "Final Action"]
    row_fmt = "{:<4} {:<20} {:<15} {:<6} {:<25} {:<8} {:<10} {:<15}"
    print(row_fmt.format(*headers))
    print("-" * 110)

    stats = {"VERIFIED": 0, "UNCERTAIN": 0, "HALLUCINATION": 0}

    for i, scen in enumerate(scenarios):
        # 1. Visual Proposal
        v_out = vis.dream(scen)
        
        # 2. Physics Context
        t_out = tel.get_context(scen)
        
        # 3. Logic Audit
        l_out = logic.audit(v_out, t_out)
        
        # 4. The Harmony Gate Verdict
        z = l_out["z_score"]
        gate_status = ""
        action = ""
        
        if z <= THRESH_VERIFIED:
            gate_status = "[OK]"
            action = "LEARN (+Weight)"
            stats["VERIFIED"] += 1
        elif z <= THRESH_REJECT:
            gate_status = "[?]"
            action = "DISCARD (Weak)"
            stats["UNCERTAIN"] += 1
        else:
            gate_status = "[X]"
            action = "BLOCK (-Weight)"
            stats["HALLUCINATION"] += 1
            
        # Formatting for display
        logic_summary = ",".join(l_out["reasons"]) if l_out["reasons"] else "NEUTRAL"
        if len(logic_summary) > 23: logic_summary = logic_summary[:20] + "..."
        
        if (i+1) % 500 == 0 or (i+1) == total_cycles:
            print(row_fmt.format(
                i+1, scen, v_out["object"], f"{v_out['confidence']:.2f}",
                logic_summary, f"{z:.2f}", gate_status, action
            ))
        
    print("\n" + "="*50)
    print(f"FINAL STATISTICS ({total_cycles} DREAMS processed)")
    print(f"VERIFIED (Truth):       {stats['VERIFIED']} (Fed. Learning Candidates)")
    print(f"UNCERTAIN (Grey Zone):  {stats['UNCERTAIN']}")
    print(f"HALLUCINATIONS (Lies):  {stats['HALLUCINATION']}")
    print("="*50)

if __name__ == "__main__":
    run_bicameral_simulation()
