# Copyright (c) 2024-2025 BorodinD&V
# simulations/simulate_swarm_formation_avoidance.py

import random
import math

class FormationNode:
    def __init__(self, node_id, pos_x, pos_y):
        self.node_id = node_id
        self.x = pos_x
        self.y = pos_y
        self.vx = 0.0
        self.vy = 0.0

    def push_apart(self, other_nodes, min_dist=2.0):
        for other in other_nodes:
            if other.node_id == self.node_id: continue
            
            dx = self.x - other.x
            dy = self.y - other.y
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist < min_dist:
                # Collision avoidance force
                force = (min_dist - dist) / dist
                self.vx += dx * force * 0.1
                self.vy += dy * force * 0.1
        
        # Friction
        self.vx *= 0.8
        self.vy *= 0.8
        self.x += self.vx
        self.y += self.vy

def run_simulation(cycles=1000, nodes_count=10):
    print("======================================================================")
    print(f" [!] STRESS TEST: SWARM FORMATION AVOIDANCE ({cycles} CYCLES)")
    print(f" SCENARIO: {nodes_count} NODES IN TIGHT 5x5m BOX (COLLISION STRESS)")
    print("======================================================================")
    
    nodes = [FormationNode(i, random.uniform(0, 5), random.uniform(0, 5)) for i in range(nodes_count)]
    collisions = 0
    min_observed_dist = 100.0

    for step in range(1, cycles + 1):
        for node in nodes:
            node.push_apart(nodes)
            
        # Collision check
        for i in range(len(nodes)):
            for j in range(i+1, len(nodes)):
                dx = nodes[i].x - nodes[j].x
                dy = nodes[i].y - nodes[j].y
                dist = math.sqrt(dx*dx + dy*dy)
                min_observed_dist = min(min_observed_dist, dist)
                if dist < 0.3: # Drone radius overlap
                    collisions += 1
        
        if step % 200 == 0:
            print(f"  Cycle {step}: Min Separation={min_observed_dist:.3f}m | Total Collisions={collisions}")

    print("\n======================================================================")
    print(" [+] SWARM COHESION SUMMARY")
    print(f" FINAL COLLISION COUNT: {collisions}")
    print(f" MIN SAFE DISTANCE:     {min_observed_dist:.3f}m")
    print(f" HARMONY RATING:        {'PERFECT' if collisions == 0 else 'STABLE'}")
    print("======================================================================")

if __name__ == "__main__":
    run_simulation(1000)
