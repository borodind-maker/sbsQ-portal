# sbsQ <-> CoppeliaSim Bridge
# Translates abstract logic commands to 3D Physics actions

import time
import math
import sys
from dataclasses import dataclass

# Try to import CoppeliaSim client (must be installed via pip)
try:
    from coppeliasim_zmqremoteapi_client import RemoteApiClient
except ImportError:
    print("Error: 'coppelia-zmqremoteapi-client' not installed.")
    print("Run: pip install coppelia-zmqremoteapi-client")
    sys.exit(1)

# Import our sbsQ Logic
try:
    from sim_physics_wire_landing import LEPWireEpisode, SensorSample1D
except ImportError:
    # Fallback for relative path running
    sys.path.append(".") 
    # In real usage, ensure PYTHONPATH is set

class CoppeliaBridge:
    def __init__(self):
        self.client = RemoteApiClient()
        self.sim = self.client.require('sim')
        
        self.drone_handle = -1
        self.target_handle = -1
        self.wire_handle = -1
        
    def connect(self):
        self.sim.startSimulation()
        print("Connected to CoppeliaSim...")
        
        # Get Handles (Assumes a scene with 'Quadricopter' and 'PowerLine')
        # You might need to adjust names based on your .ttt scene
        try:
            self.drone_handle = self.sim.getObject('/Quadricopter')
            self.target_handle = self.sim.getObject('/Quadricopter/target')
            self.wire_handle = self.sim.getObject('/PowerLine')
        except:
            print("Warning: Standard objects not found. Using placeholders.")

    def sync_state(self, logic_ep: 'LEPWireEpisode'):
        """
        Reads CoppeliaSim state and updates the Math Logic Class
        """
        # Get Position
        pos = self.sim.getObjectPosition(self.drone_handle, -1)
        # Coppelia Z is up, Logic Z might be relative to wire
        
        # Let's say wire is at (0,0,5) in World
        # Logic y = horizontal offset, z = vertical distance from wire
        
        wire_pos = self.sim.getObjectPosition(self.wire_handle, -1) if self.wire_handle != -1 else [0, 0, 5]
        
        current_y_offset = pos[1] - wire_pos[1]
        current_z_dist = pos[2] - wire_pos[2]
        
        # Inject into logic class (overriding its internal dead-reckoning for this step)
        # This is "Hardware-in-the-Loop" style simulation
        return current_y_offset, current_z_dist

    def apply_action(self, vy_cmd, vz_cmd, dt):
        """
        Applies logic velocity commands to physical drone target
        """
        if self.target_handle == -1:
            return
            
        pos = self.sim.getObjectPosition(self.target_handle, -1)
        new_pos = [
            pos[0], 
            pos[1] + vy_cmd * dt, 
            pos[2] + vz_cmd * dt # Z is Up
        ]
        self.sim.setObjectPosition(self.target_handle, -1, new_pos)

    def stop(self):
        self.sim.stopSimulation()
        print("Simulation stopped.")

def demo_run():
    bridge = CoppeliaBridge()
    bridge.connect()
    
    # Initialize Logic
    # We use our existing class but will override its "physics" loop
    # with real data from CoppeliaSim
    logic_ep = None # Initialize your LEPWireEpisode here
    
    print("Running visual demonstration...")
    # This loop replaces the internal logical loop
    for i in range(500):
        t0 = time.time()
        
        # 1. Read Sensors from Sim
        y, z = bridge.sync_state(None) # Pass logic obj if needed
        
        # 2. Run sbsQ Gate Logic (Abstracted here)
        # ... logic.decide(y, z) ...
        # Assume logic returns velocity commands
        vy_cmd = -y * 0.5 # Simple P-controller for demo
        vz_cmd = -0.1     # Slow descent
        
        # 3. Apply to Sim
        bridge.apply_action(vy_cmd, vz_cmd, 0.05)
        
        # Sync time
        self.sim.step() # Explicit stepping if in synchronous mode
        time.sleep(0.05)
        
    bridge.stop()

if __name__ == "__main__":
    demo_run()
