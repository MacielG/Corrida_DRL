#!/usr/bin/env python3
"""Teste de detecção de checkpoint."""
import sys
import numpy as np
from environment import CorridaEnv

env = CorridaEnv(map_type="corridor")
obs, info = env.reset()

print(f"Checkpoint: {env.checkpoints[0]}")
print(f"Start pos: {env.car1_pos}\n")

for step in range(150):
    obs, reward, done, truncated, info = env.step(0)  # acelera
    
    if step % 20 == 0 or info["success"]:
        checkpoint = env.checkpoints[env.checkpoint_index] if env.checkpoint_index < len(env.checkpoints) else None
        dist = np.sqrt((env.car1_pos[0] - checkpoint[0])**2 + (env.car1_pos[1] - checkpoint[1])**2) if checkpoint else -1
        print(f"Step {step:3d}: Checkpoint {info['checkpoint']}, Success: {info['success']}, "
              f"Dist: {dist:7.1f}, Reward: {reward:7.3f}, Speed: {env.car1_speed:6.2f}")
    
    if done:
        print("\nDone!")
        break

print(f"\nCheckpoints reached: {env.checkpoints_reached}")
print(f"Final checkpoint_index: {env.checkpoint_index}")
