#!/usr/bin/env python3
"""Teste rápido do sistema de recompensa corrigido."""
import sys
import numpy as np
from environment import CorridaEnv

def test_rewards():
    print("\n=== TESTE DE RECOMPENSA CORRIGIDA ===\n")
    
    env = CorridaEnv(map_type="corridor", car_stats={"accel": 0.5, "turn_speed": 5.0, "max_speed": 20.0})
    obs, info = env.reset()
    
    print(f"Checkpoint inicial: {env.checkpoints[env.checkpoint_index]}")
    print(f"Posição inicial: {env.car1_pos}")
    print(f"Velocidade inicial: {env.car1_speed}\n")
    
    # Simula 30 steps de movimento
    for step in range(30):
        action = 0  # Sempre acelerar
        obs, reward, done, truncated, info = env.step(action)
        
        print(f"Step {step+1:2d} | Reward: {reward:7.3f} | Speed: {env.car1_speed:6.3f} | "
              f"Pos: ({env.car1_pos[0]:7.1f}, {env.car1_pos[1]:7.1f}) | "
              f"Checkpoint: {env.checkpoint_index}")
        
        if done:
            print("\n✓ Episódio terminado!")
            break
    
    print(f"\n Final Speed: {env.car1_speed:.3f}")
    print(f"Final Distance to checkpoint: {np.linalg.norm(np.array(env.car1_pos) - np.array(env.checkpoints[env.checkpoint_index])) if env.checkpoint_index < len(env.checkpoints) else 'N/A'}")
    print("\nO agente deveria estar se movendo para frente (velocidade > 0)")
    print("e recebendo recompensas positivas por movimento e progresso.")

if __name__ == "__main__":
    test_rewards()
