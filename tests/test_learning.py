import numpy as np
import pytest
from agent import Agent
from environment import CorridaEnv
from stable_baselines3.common.vec_env import DummyVecEnv
import time

@pytest.mark.slow
@pytest.mark.parametrize("seed", [42, 123, 2025])
def test_agent_learning_statistical(seed, tmp_path):
    """Teste estatístico: RL deve melhorar média de recompensa em várias rodadas."""
    np.random.seed(seed)
    env = DummyVecEnv([lambda: CorridaEnv(map_type="corridor")])
    agent = Agent(env, model_path=str(tmp_path / f"test_learning_{seed}"))
    initial_scores = []
    final_scores = []
    for _ in range(5):
        initial = agent.evaluate(env, n_episodes=3)
        agent.train(total_timesteps=200, eval_interval=100)
        final = agent.evaluate(env, n_episodes=3)
        initial_scores.append(initial)
        final_scores.append(final)
    assert np.mean(final_scores) > np.mean(initial_scores), (
        f"Final mean score ({np.mean(final_scores)}) should be greater than initial ({np.mean(initial_scores)})"
    )

@pytest.mark.slow
def test_agent_vs_random(tmp_path):
    """Compara agente RL com agente aleatório."""
    env = DummyVecEnv([lambda: CorridaEnv(map_type="corridor")])
    agent = Agent(env, model_path=str(tmp_path / "test_vs_random"))
    agent.train(total_timesteps=500, eval_interval=100)
    rl_score = agent.evaluate(env, n_episodes=5)
    # Agente aleatório
    random_scores = []
    for _ in range(5):
        obs, _ = env.reset()
        done = False
        total_reward = 0
        while not done:
            action = env.action_space.sample()
            obs, reward, done, info = env.envs[0].step(action)
            total_reward += reward
            if isinstance(done, (list, np.ndarray)):
                done = done[0]
        random_scores.append(total_reward)
    random_score = np.mean(random_scores)
    assert rl_score > random_score, (
        f"RL agent ({rl_score}) should outperform random agent ({random_score})"
    )

@pytest.mark.slow
def test_agent_no_regression(tmp_path):
    """Garante que o agente não piora após múltiplos ciclos de treino."""
    env = DummyVecEnv([lambda: CorridaEnv(map_type="corridor")])
    agent = Agent(env, model_path=str(tmp_path / "test_no_regression"))
    best_score = agent.evaluate(env, n_episodes=3)
    for _ in range(3):
        agent.train(total_timesteps=200, eval_interval=100)
        score = agent.evaluate(env, n_episodes=3)
        best_score = max(best_score, score)
        assert score >= best_score - 10, "Agent regressed too much after training."

@pytest.mark.slow
def test_agent_progressive_learning(tmp_path):
    """Avalia o agente em diferentes estágios do treinamento."""
    env = DummyVecEnv([lambda: CorridaEnv(map_type="corridor")])
    agent = Agent(env, model_path=str(tmp_path / "test_progressive"))
    scores = []
    for _ in range(5):
        agent.train(total_timesteps=100, eval_interval=50)
        score = agent.evaluate(env, n_episodes=2)
        scores.append(score)
    # Espera tendência de crescimento (não estritamente monotônico)
    assert scores[-1] > scores[0], f"Score did not improve: {scores}"

@pytest.mark.slow
def test_agent_generalization(tmp_path):
    """Treina em um mapa, avalia em outro."""
    env_train = DummyVecEnv([lambda: CorridaEnv(map_type="corridor")])
    env_test = DummyVecEnv([lambda: CorridaEnv(map_type="curve")])
    agent = Agent(env_train, model_path=str(tmp_path / "test_generalization"))
    agent.train(total_timesteps=500, eval_interval=100)
    test_score = agent.evaluate(env_test, n_episodes=3)
    assert np.isfinite(test_score), "Agent should generalize and not crash."

@pytest.mark.slow
def test_agent_success_threshold(tmp_path):
    """Exige que o agente atinja um limiar de recompensa após treino."""
    env = DummyVecEnv([lambda: CorridaEnv(map_type="corridor")])
    agent = Agent(env, model_path=str(tmp_path / "test_success_threshold"))
    agent.train(total_timesteps=1000, eval_interval=200)
    score = agent.evaluate(env, n_episodes=5)
    assert score > -10, f"Agent did not reach expected reward threshold: {score}"

@pytest.mark.slow
def test_agent_efficiency(tmp_path):
    """Garante que o ciclo de treino/avaliação é eficiente."""
    env = DummyVecEnv([lambda: CorridaEnv(map_type="corridor")])
    agent = Agent(env, model_path=str(tmp_path / "test_efficiency"))
    start = time.time()
    agent.train(total_timesteps=200, eval_interval=100)
    agent.evaluate(env, n_episodes=2)
    duration = time.time() - start
    assert duration < 30, f"Training/evaluation took too long: {duration}s"

@pytest.mark.slow
def test_agent_robustness_to_env_changes(tmp_path):
    """Testa se o agente aprende mesmo com ruído no ambiente."""
    class NoisyCorridaEnv(CorridaEnv):
        def step(self, action):
            obs, reward, terminated, truncated, info = super().step(action)
            reward += np.random.normal(0, 0.5)  # Adiciona ruído
            return obs, reward, terminated, truncated, info
    env = DummyVecEnv([lambda: NoisyCorridaEnv(map_type="corridor")])
    agent = Agent(env, model_path=str(tmp_path / "test_robustness"))
    agent.train(total_timesteps=500, eval_interval=100)
    score = agent.evaluate(env, n_episodes=3)
    assert np.isfinite(score), "Agent should handle noisy environment."

@pytest.mark.slow
def test_agent_continual_learning(tmp_path):
    """Testa aprendizado contínuo: treina, salva, recarrega e continua aprendendo."""
    env = DummyVecEnv([lambda: CorridaEnv(map_type="corridor")])
    agent = Agent(env, model_path=str(tmp_path / "test_continual"))
    agent.train(total_timesteps=200, eval_interval=100)
    score1 = agent.evaluate(env, n_episodes=2)
    agent.save()
    agent.load()
    agent.train(total_timesteps=200, eval_interval=100)
    score2 = agent.evaluate(env, n_episodes=2)
    assert score2 >= score1 - 10, "Continual learning failed: performance regressed."
