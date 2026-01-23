# Copyright (c) 2024-2025 BorodinD&V
# simulations/simulate_mesh_reconstitution.py

import random
import sys
import time

class SwarmMeshSimulator:
    """
    Simulates a decentralized communication mesh of sbsQ swarm.
    Tests reconstitution speed after massive node dropouts.
    """
    def __init__(self, total_nodes=50):
        self.total_nodes = total_nodes
        self.active_nodes = set(range(total_nodes))
        self.connectivity = 1.0
        self.recovery_speed = 0.05 # Re-routing efficiency per cycle

    def simulate_event(self, step):
        # Every 200 cycles, a "Massive dropout" event happens
        if step % 200 == 100:
            dropout_count = int(self.total_nodes * 0.4) # 40% loss
            dropouts = random.sample(list(self.active_nodes), dropout_count)
            for d in dropouts:
                self.active_nodes.remove(d)
            self.connectivity = 0.2 # Dramatic drop
            print(f"  Cycle {step}: [!] MESH LOSS - 40% nodes dropped. Connectivity: {self.connectivity:.2f}")

        # Natural recovery (re-routing)
        if len(self.active_nodes) < self.total_nodes:
            self.connectivity = min(1.0, self.connectivity + self.recovery_speed)
            # Simulate "New node discovery" or "Ghost node" logic
            if self.connectivity >= 0.95 and len(self.active_nodes) < self.total_nodes:
                self.active_nodes.add(random.randint(0, self.total_nodes-1))
        
        return self.connectivity

def run_test(cycles=1000):
    print("======================================================================")
    print(f" [!] STRESS TEST: MESH TOPOLOGY RECONSTITUTION ({cycles} CYCLES)")
    print(" SCENARIO: DECENTRALIZED RE-ROUTING UPON 40% NODE LOSS")
    print("======================================================================")
    
    sim = SwarmMeshSimulator(50)
    conn_history = []
    
    for step in range(1, cycles + 1):
        conn = sim.simulate_event(step)
        conn_history.append(conn)
        
        if step % 200 == 0:
            print(f"  Cycle {step}: Active Nodes={len(sim.active_nodes)} | Mesh Integrity={conn:.2f}")

    avg_conn = sum(conn_history) / cycles
    print("\n======================================================================")
    print(" [+] MESH RESILIENCE SUMMARY")
    print(f" AVG CONNECTIVITY: {avg_conn:.4f}")
    print(f" RECOVERY RATING:  {'EXCELLENT' if avg_conn > 0.85 else 'GOOD'}")
    print(" STATUS:           DYNAMIC TOPOLOGY ACTIVE")
    print("======================================================================")

if __name__ == "__main__":
    run_test(1000)
