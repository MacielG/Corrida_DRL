import matplotlib.pyplot as plt
import numpy as np
import os
from config import ENV_SCALE, RL_ALGORITHM, SUPPORTED_ALGORITHMS
from environment import CorridaEnv
from agent import Agent
from stable_baselines3.common.vec_env import DummyVecEnv

def run_experiment(algorithm, map_type="corridor", total_timesteps=10000, n_parallel=4):
    os.environ["RL_ALGORITHM"] = algorithm
    env = DummyVecEnv([lambda: CorridaEnv(map_type=map_type) for _ in range(n_parallel)])
    agent = Agent(env, model_path=f"models/model_{map_type}_{algorithm}")
    rewards = []
    obs = env.reset()
    for _ in range(total_timesteps):
        # CORREÇÃO: Predição vetorizada é 8-10x mais rápida
        actions_array, _ = agent.model.predict(obs, deterministic=False)
        actions = [int(a) for a in actions_array]
        obs, reward, dones, infos = env.step(actions)
        rewards.append(np.mean(reward))
    return rewards

def main():
    os.makedirs("docs", exist_ok=True)
    results = {}
    for alg in SUPPORTED_ALGORITHMS:
        print(f"Treinando com {alg}...")
        rewards = run_experiment(alg, map_type="corridor", total_timesteps=10000, n_parallel=4)
        results[alg] = rewards
    # Plot
    plt.figure(figsize=(10,6))
    for alg, rewards in results.items():
        if len(rewards) < 100:  # Skip if too few rewards
            continue
        ma = np.convolve(rewards, np.ones(100)/100, mode='valid')
        plt.plot(ma, label=alg)
    plt.title("Comparação de Algoritmos RL - Corrida DRL")
    plt.xlabel("Passos")
    plt.ylabel("Recompensa Média (100 passos)")
    plt.legend()
    plt.grid()
    plt.savefig("docs/comparison.png")
    # Markdown
    with open("docs/comparison.md", "w", encoding="utf-8") as f:
        f.write("# Comparação de Algoritmos RL\n\n")
        f.write("Experimento: Corrida DRL, 10.000 passos, mapa 'corridor', 4 ambientes paralelos.\n\n")
        f.write("![Gráfico de comparação](comparison.png)\n\n")
        for alg in SUPPORTED_ALGORITHMS:
            rewards = results[alg]
            final_avg = np.mean(rewards[-100:]) if rewards else 0.0
            f.write(f"- {alg}: Recompensa final média: {final_avg:.2f}\n")

if __name__ == "__main__":
    main()
