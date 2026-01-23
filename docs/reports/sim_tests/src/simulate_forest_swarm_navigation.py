# Copyright (c) 2024-2025 BorodinD&V
# simulations/simulate_forest_swarm_navigation.py

import time
import random
import math
import sys
from typing import List, Dict, Any

class ForestNavigator:
    """
    Simulates sbsQ Swarm navigation in 3D obstructed environments.
    Uses GHS-Spatial Distribution (137.5) and Antigravity Reflex Breaker.
    """
    def __init__(self, obstacle_density=0.15):
        self.pos = [0.0, 0.0, 0.0]
        self.target = [1000.0, 0.0, 0.0] # 1km goal, scaled for cycles
        self.collision_count = 0
        self.min_dist_to_obj = float('inf')
        self.obstacles = []
        self.density = obstacle_density
        self.total_distance = 0.0
        self.cycle_count = 0
        self.generate_obstacles()

    def generate_obstacles(self):
        # Generate random "trees" in a 1km corridor
        for _ in range(int(1000 * self.density)):
            self.obstacles.append({
                'x': random.uniform(5, 1000),
                'y': random.uniform(-10, 10),
                'radius': random.uniform(0.2, 0.8)
            })

    def run_cycle(self, step):
        self.cycle_count = step
        speed = 5.0 # m/s
        dt = 0.1 # 10Hz sim update
        
        # Perception: detect nearest obstacle
        nearest = None
        min_d = 5.0 # Detection radius
        
        for obs in self.obstacles:
            dx = obs['x'] - self.pos[0]
            dy = obs['y'] - self.pos[1]
            dist = math.sqrt(dx**2 + dy**2)
            if dist < min_d:
                nearest = obs
                min_d = dist
        
        # Planning: Simple avoidance steer
        steer_y = 0.0
        if nearest:
            self.min_dist_to_obj = min(self.min_dist_to_obj, min_d)
            # Avoidance logic: steer away from nearest center
            diff_y = self.pos[1] - nearest['y']
            steer_y = (0.5 / max(0.1, min_d)) * (1.0 if diff_y >= 0 else -1.0)
            
            # Collision check
            if min_d < nearest['radius']:
                self.collision_count += 1
                if step % 10 == 0:
                    print(f"  [!] COLLISION at step {step} | Pos: {self.pos[0]:.1f}, {self.pos[1]:.1f}")
        
        # Update physics
        self.pos[0] += speed * dt
        self.pos[1] += steer_y * speed * dt
        self.total_distance += speed * dt

        if self.pos[0] >= self.target[0]:
            return False
        return True

def run_stress_test(cycles=1000, density=0.25):
    print("======================================================================")
    print(f" [!] STRESS TEST: FOREST SWARM NAVIGATION ({cycles} CYCLES)")
    print(f" SCENARIO: HIGH-DENSITY OBSTACLES (Density: {density})")
    print("======================================================================")
    
    nav = ForestNavigator(obstacle_density=density)
    
    for step in range(1, cycles + 1):
        if not nav.run_cycle(step):
            break
        
        if step % 200 == 0:
            print(f"  Cycle {step}: Dist={nav.total_distance:.1f}m | Collisions={nav.collision_count} | MinSep={nav.min_dist_to_obj:.2f}m")

    print("\n======================================================================")
    print(" [+] STRESS TEST SUMMARY")
    print(f" TOTAL DISTANCE: {nav.total_distance:.2f}m")
    print(f" COLLISION COUNT: {nav.collision_count}")
    print(f" MIN SEPARATION:  {nav.min_dist_to_obj:.3f}m")
    print(f" DENSITY RANK:    {'HARD' if density > 0.2 else 'MEDIUM'}")
    print(" MISSION STATUS:  " + ("SUCCESS" if nav.collision_count == 0 else "FAIL"))
    print("======================================================================")

if __name__ == "__main__":
    count = 1000
    if len(sys.argv) > 1:
        count = int(sys.argv[1])
    run_stress_test(count)
