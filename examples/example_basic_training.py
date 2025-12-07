"""Exemplo básico: Treinar um agente simples em um mapa."""

import sys
import os

# Adiciona diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from environment import CorridaEnv
from agent import Agent
import numpy as np


def example_basic_training():
    """Treina um agente básico em um corredor."""
    
    print("=" * 60)
    print("EXEMPLO 1: Treinamento Básico")
    print("=" * 60)
    
    # 1. Criar ambiente
    print("\n[1] Criando ambiente...")
    env = CorridaEnv(map_type="corridor", reward_shaper_type='balanced')
    print(f"✅ Ambiente criado!")
    print(f"   - Observation space: {env.observation_space.shape}")
    print(f"   - Action space: {env.action_space.n}")
    
    # 2. Criar agente
    print("\n[2] Criando agente...")
    agent = Agent(env, model_path="models/basic_train")
    print("✅ Agente criado (PPO com Stable Baselines3)")
    
    # 3. Treino
    print("\n[3] Iniciando treino (50k timesteps)...")
    agent.train(total_timesteps=50000)
    print("✅ Treino completo!")
    
    # 4. Avaliação
    print("\n[4] Avaliando agente...")
    obs, _ = env.reset()
    episode_reward = 0
    episode_length = 0
    
    for step in range(500):
        action, _ = agent.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        episode_reward += reward
        episode_length += 1
        
        if terminated or truncated:
            break
    
    print(f"✅ Episódio completo!")
    print(f"   - Recompensa: {episode_reward:.2f}")
    print(f"   - Comprimento: {episode_length} steps")
    print(f"   - Checkpoints atingidos: {info['checkpoint']}")
    
    # 5. Salvar
    print("\n[5] Salvando modelo...")
    agent.save("models/basic_train_final.zip")
    print("✅ Modelo salvo em models/basic_train_final.zip")
    
    print("\n" + "=" * 60)
    print("✨ Exemplo completo!")
    print("=" * 60)


def example_compare_reward_shapers():
    """Compara diferentes reward shapers."""
    
    print("\n" + "=" * 60)
    print("EXEMPLO 2: Comparar Reward Shapers")
    print("=" * 60)
    
    shapers = ['balanced', 'speed', 'safety']
    results = {}
    
    for shaper_type in shapers:
        print(f"\n[{shaper_type.upper()}] Treinando com {shaper_type} shaper...")
        
        # Criar ambiente com shaper
        env = CorridaEnv(map_type="corridor", reward_shaper_type=shaper_type)
        
        # Treino rápido
        agent = Agent(env, model_path=f"models/compare_{shaper_type}")
        agent.train(total_timesteps=20000)
        
        # Avaliação
        rewards = []
        for _ in range(5):
            obs, _ = env.reset()
            episode_reward = 0
            done = False
            
            while not done:
                action, _ = agent.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                episode_reward += reward
                done = terminated or truncated
            
            rewards.append(episode_reward)
        
        avg_reward = np.mean(rewards)
        std_reward = np.std(rewards)
        results[shaper_type] = (avg_reward, std_reward)
        
        print(f"   Recompensa: {avg_reward:.2f} ± {std_reward:.2f}")
    
    # Resumo
    print("\n" + "-" * 60)
    print("RESUMO:")
    for shaper_type, (avg, std) in results.items():
        print(f"  {shaper_type:10s}: {avg:7.2f} ± {std:5.2f}")
    
    best = max(results.items(), key=lambda x: x[1][0])
    print(f"\n✨ Melhor: {best[0]} com {best[1][0]:.2f}")
    print("=" * 60)


def example_test_different_maps():
    """Treina e testa em diferentes mapas."""
    
    print("\n" + "=" * 60)
    print("EXEMPLO 3: Diferentes Mapas")
    print("=" * 60)
    
    maps = ['corridor', 'curve', 'circle']
    
    for map_type in maps:
        print(f"\n[{map_type.upper()}] Testando mapa '{map_type}'...")
        
        # Ambiente
        env = CorridaEnv(map_type=map_type)
        
        # Teste com ações aleatórias
        obs, _ = env.reset()
        rewards = []
        
        for _ in range(100):
            action = env.action_space.sample()
            obs, reward, done, _, info = env.step(action)
            rewards.append(reward)
            
            if done:
                break
        
        avg_reward = np.mean(rewards)
        print(f"   Recompensa média: {avg_reward:.2f}")
        print(f"   Checkpoints: {info['checkpoint']}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Execute os exemplos
    example_basic_training()
    example_compare_reward_shapers()
    example_test_different_maps()
    
    print("\n✨ Todos os exemplos executados com sucesso!")
