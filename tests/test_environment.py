import pytest
import os
import numpy as np
from environment import CorridaEnv
from agent import Agent, LogCallback, CustomCallback
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3 import DQN, PPO, SAC
from config import SUPPORTED_ALGORITHMS, load_config, ENV_SCALE
from compare_algorithms import run_experiment, main as compare_main
from metrics import Metrics
import matplotlib.pyplot as plt
from unittest.mock import Mock

@pytest.mark.parametrize("algo", ["DQN", "PPO", "SAC"])
def test_agent_save_and_load(tmp_path, algo, monkeypatch):
    os.environ["RL_ALGORITHM"] = algo
    env = DummyVecEnv([lambda: CorridaEnv(map_type="corridor")])
    agent_instance = Agent(env, model_path=str(tmp_path / f"test_model_{algo}"))
    # Mock the model's save method to avoid disk access
    monkeypatch.setattr(agent_instance.model, "save", lambda path=None: None)
    # Mock the Agent.load method to avoid disk access
    monkeypatch.setattr(agent_instance, "load", lambda path: None)
    agent_instance.save()
    agent_instance.load(str(tmp_path / f"test_model_{algo}"))
    assert agent_instance.model is not None

def test_agent_train_calls_learn(monkeypatch):
    env = DummyVecEnv([lambda: CorridaEnv(map_type="corridor")])
    agent_instance = Agent(env)
    called = {}
    monkeypatch.setattr(agent_instance.model, "learn", lambda *a, **k: called.setdefault("learn", True))
    monkeypatch.setattr(agent_instance, "evaluate", lambda *a, **k: 0)
    agent_instance.train(total_timesteps=1, eval_interval=1)
    assert called.get("learn")

def test_agent_model_initialization():
    env = DummyVecEnv([lambda: CorridaEnv(map_type="corridor")])
    agent = Agent(env)
    assert agent.model is not None

@pytest.mark.parametrize("algo", ["DQN", "PPO", "SAC"])
def test_agent_evaluate_multi_episodes(algo):
    os.environ["RL_ALGORITHM"] = algo
    env = DummyVecEnv([lambda: CorridaEnv(map_type="corridor")])
    agent = Agent(env, model_path="models/test_eval")
    agent.model.predict = lambda state, deterministic=False: (np.array(0), None)
    score = agent.evaluate(env, n_episodes=5)
    assert isinstance(score, float)
    assert np.isfinite(score)

def test_log_callback():
    callback = LogCallback(verbose=1)
    callback.rewards = [1.0] * 1000
    callback._on_step()
    assert len(callback.rewards) == 1001  # Account for the additional reward

def test_custom_callback(monkeypatch):
    callback = CustomCallback()
    env = DummyVecEnv([lambda: CorridaEnv(map_type="corridor")])
    env.envs[0].car1_speed = 2.0
    # Mock para simular training_env.get_attr
    monkeypatch.setattr(callback, "get_attr", lambda name: [2.0] if name == "car1_speed" else [None])
    callback.logger = Mock(record=lambda key, value: None)
    assert callback._on_step()

def test_run_experiment_error(monkeypatch):
    def mock_env_init(*args, **kwargs):
        raise RuntimeError("Erro na inicialização")
    monkeypatch.setattr("environment.CorridaEnv.__init__", mock_env_init)
    with pytest.raises(RuntimeError):
        run_experiment("DQN", map_type="corridor", total_timesteps=100)

def test_main_empty_results(monkeypatch, tmp_path):
    monkeypatch.setattr("compare_algorithms.run_experiment", lambda *a, **k: [])
    monkeypatch.setattr(plt, "figure", lambda *a, **k: None)
    monkeypatch.setattr(plt, "plot", lambda *a, **k: None)
    monkeypatch.setattr(plt, "title", lambda *a, **k: None)
    monkeypatch.setattr(plt, "xlabel", lambda *a, **k: None)
    monkeypatch.setattr(plt, "ylabel", lambda *a, **k: None)
    monkeypatch.setattr(plt, "legend", lambda *a, **k: None)
    monkeypatch.setattr(plt, "grid", lambda *a, **k: None)
    monkeypatch.setattr(plt, "savefig", lambda *a, **k: None)
    
    compare_main()
    assert os.path.exists("docs/comparison.md")

def test_load_config_missing_file(tmp_path):
    cfg = load_config(str(tmp_path / "nonexistent.json"))
    assert cfg["learning_rate"] == 0.0003
    assert cfg["map_type"] == "corridor"

def test_load_config_invalid_json(tmp_path):
    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{invalid json")
    cfg = load_config(str(invalid_json))
    assert cfg["learning_rate"] == 0.0003

def test_reset_randomize_checkpoint():
    env = CorridaEnv(map_type="corridor")
    state, info = env.reset(randomize_checkpoint=True)
    assert len(env.checkpoints) == 1
    assert 220 * ENV_SCALE <= env.checkpoints[0][1] <= 380 * ENV_SCALE

def test_reset_randomize_start_failure(monkeypatch):
    env = CorridaEnv(map_type="corridor")
    def mock_is_on_corridor(self, pos):
        return False
    monkeypatch.setattr(CorridaEnv, "is_on_corridor", mock_is_on_corridor)
    with pytest.raises(Exception, match="Não foi possível inicializar"):
        env.reset()

def test_step_empty_checkpoints():
    env = CorridaEnv(map_type="corridor")
    env.checkpoints = []
    state, reward, terminated, truncated, info = env.step(0)
    assert isinstance(state, np.ndarray)
    assert isinstance(reward, float)
    assert info["checkpoint"] == 0

def test_circle_map_specific():
    env = CorridaEnv(map_type="circle")
    env.reset()
    cp = env.checkpoints[1]
    assert abs(cp[0] - 400 * ENV_SCALE) < 1e-6
    assert abs(cp[1] - (300 * ENV_SCALE + 200 * ENV_SCALE)) < 1e-6
    inner_point = (400 * ENV_SCALE + 150 * ENV_SCALE, 300 * ENV_SCALE)
    assert env.is_on_corridor(inner_point)

def test_metrics_render_empty(interface):
    m = Metrics()
    m.render(interface.screen, render_interval=1)
    assert interface.screen.get_at((550, 10)) == (255, 255, 255, 255)

def test_metrics_render_small_data(interface):
    m = Metrics()
    for i in range(5):
        m.update(i, i % 2, checkpoint=i % 3)
    m.render(interface.screen, render_interval=1)
    assert interface.screen.get_at((550, 10)) == (255, 255, 255, 255)

def test_metrics_memory_cleanup():
    m = Metrics()
    for i in range(1001):
        m.update(i, i % 2, episode_time=1.0, checkpoint=i % 3)
    assert len(m.rewards) <= 100
    assert len(m.collisions) <= 100
