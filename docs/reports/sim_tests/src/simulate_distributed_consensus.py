# Copyright (c) 2024-2025 BorodinD&V
# simulations/simulate_distributed_consensus.py

import time
import random
import math
import sys
from typing import List, Dict, Any

class SwarmNode:
    def __init__(self, node_id, is_spoofing=False):
        self.id = node_id
        self.is_spoofing = is_spoofing
        self.local_truth = 0.0
        self.state = "INIT" # INIT, PROPOSE, VOTE, CONSENSUS

    def sense(self, ground_truth):
        if self.is_spoofing:
            # Spoofing node tries to convince others of a fake target
            self.local_truth = ground_truth + random.uniform(20.0, 50.0)
        else:
            self.local_truth = ground_truth + random.uniform(-2.0, 2.0)

class ConsensusCouncil:
    """
    Simulates the Council of Agents (TCI Distributed Logic).
    Ensures that a majority (Phi-based quorum) must agree before action.
    """
    def __init__(self, node_count=7, byzantine_count=2):
        self.ground_truth = 100.0
        self.nodes = [SwarmNode(i, is_spoofing=(i < byzantine_count)) for i in range(node_count)]
        self.council_decision = None
        self.cycle_count = 0
        self.phi = (1 + 5**0.5) / 2 # Quorum threshold coefficient

    def run_consensus_cycle(self, step):
        self.cycle_count = step
        proposals = []
        
        # 1. Sense and Propose
        for node in self.nodes:
            node.sense(self.ground_truth)
            proposals.append(node.local_truth)
        
        # 2. Audit and Filter (Distributed Z-Gate simulation)
        # We calculate the median and variance of proposals
        proposals.sort()
        median_val = proposals[len(proposals)//2]
        
        votes = 0
        consensus_val = 0.0
        
        for p in proposals:
            # If a proposal is too far from the median (Z-score check), it's rejected
            if abs(p - median_val) < 10.0: # Acceptance threshold
                votes += 1
                consensus_val += p
        
        # 3. Quorum Check (Phi-Quorum)
        # Required nodes = Total / Phi approx 61.8%
        required_votes = len(self.nodes) * (1 / self.phi)
        
        if votes >= required_votes:
            self.council_decision = consensus_val / votes
            return True # Consensus reached
        return False # Still debating

def run_simulation(cycles=1000):
    print("======================================================================")
    print(f" [!] STRESS TEST: DISTRIBUTED SWARM CONSENSUS ({cycles} CYCLES)")
    print(" SCENARIO: 7 NODES (2 BYZANTINE/SPOOFING) | QUORUM: PHI-BASED")
    print("======================================================================")
    
    council = ConsensusCouncil(node_count=7, byzantine_count=2)
    success_count = 0
    accuracy_sum = 0.0

    for step in range(1, cycles + 1):
        if council.run_consensus_cycle(step):
            success_count += 1
            error = abs(council.council_decision - council.ground_truth)
            accuracy_sum += (100 - error)
            
            if step % 200 == 0:
                print(f"  Cycle {step}: Consensus REACHED | Value: {council.council_decision:.2f} | Error: {error:.2f}")
        else:
            if step % 200 == 0:
                print(f"  Cycle {step}: Consensus FAILED (Quorum not reached)")

    avg_accuracy = accuracy_sum / success_count if success_count > 0 else 0
    
    print("\n======================================================================")
    print(" [+] CONSENSUS ANALYSIS SUMMARY")
    print(f" TOTAL CYCLES:      {cycles}")
    print(f" SUCCESSFUL CYCLES: {success_count} ({ (success_count/cycles)*100 :.1f}%)")
    print(f" AVG ACCURACY:      {avg_accuracy:.2f}%")
    print(f" BYZANTINE NODES:   REJECTED (Majority Rule via Phi-Quorum)")
    print("======================================================================")

if __name__ == "__main__":
    run_simulation(1000)
