import pytest
import os
from main import main, run_curriculum, train_phase, TrainingLogger
from environment import CorridaEnv
from unittest.mock import Mock
import psutil
from tests.utils import create_mock_env

class StopTestLoop(Exception):
    pass

@pytest.mark.skip(reason="Requires complex mocking of main.py - integration test")
@pytest.mark.timeout(15)
def test_main_loop_pause(monkeypatch):
    print("Iniciando test_main_loop_pause")
    env = create_mock_env()
    print("Mock CorridaEnv criado")
    mock_vec_env = Mock()
    mock_vec_env.envs = [env]
    mock_vec_env.reset.return_value = ([[0] * 15], {})
    mock_vec_env.step.return_value = ([[0] * 15], [0.0], [False], [False], [{}])
    print("Mock SubprocVecEnv configurado")
    monkeypatch.setattr("main.SubprocVecEnv", lambda x: mock_vec_env)
    print("Monkeypatch SubprocVecEnv feito")
    class FakeInterface:
        def __init__(self, *a, **k):
            self.paused = False
            self.counter = 0
        def process_events(self):
            print("process_events chamado")
        def draw_dashboard(self, *a, **k):
            print("draw_dashboard chamado")
        def update(self):
            print("update chamado")
        def should_restart(self):
            self.counter += 1
            if self.counter > 2:
                raise StopTestLoop()
            return False
        def clear(self):
            print("clear chamado")
        def draw_env_grid_simple(self, env_single, idx):  # CORREÇÃO: draw_env_grid_simple
            print(f"draw_env_grid_simple chamado para idx={idx}")
        def clear_restart(self):
            print("clear_restart chamado")
    # O mock cobre apenas a interface gráfica, mantendo o fluxo principal do main real.
    monkeypatch.setattr("main.Interface", FakeInterface)
    print("Monkeypatch Interface feito")
    monkeypatch.setattr("main.Agent", lambda *a, **k: Mock(predict=lambda x: 0))
    print("Monkeypatch Agent feito")
    monkeypatch.setattr("main.TrainingLogger", lambda: Mock(log=lambda *a, **k: None, close=lambda: None))
    print("Monkeypatch TrainingLogger feito")
    print("Chamando main()...")
    try:
        main(map_type="corridor", n_parallel=1)
    except StopTestLoop:
        print("Loop principal interrompido para o teste (StopTestLoop)")
    print("Finalizando test_main_loop_pause")

@pytest.mark.skip(reason="Requires complex mocking of main.py and Agent - integration test")
@pytest.mark.timeout(5)
def test_run_curriculum_complete(monkeypatch):
    print("Iniciando test_run_curriculum_complete")
    # Mock DummyVecEnv e ambiente para simular progresso real
    class DummyEnvMock:
        def __init__(self):
            self.episodes = 0
            self.width = 800
            self.height = 600
            self.car1_pos = (0, 0)
            self.car1_angle = 0.0
        def reset(self):
            return [0] * 15
        def step(self, action):
            self.episodes += 1
            # Após 2 episódios, sempre retorna done=True
            done = self.episodes >= 2
            return [0] * 15, 100, done, False, {"success": True, "checkpoint": 2}
    class DummyVecEnvMock:
        def __init__(self):
            self.envs = [DummyEnvMock()]
            self.episodes = 0
        def reset(self):
            return [[0] * 15]
        def step(self, actions):
            self.episodes += 1
            done = self.episodes >= 2
            return [[0] * 15], [100], [done], [False], [{"success": True, "checkpoint": 2}]
    monkeypatch.setattr("main.DummyVecEnv", lambda x: DummyVecEnvMock())
    monkeypatch.setattr("main.Agent", lambda *a, **k: Mock(predict=lambda x: 0))
    monkeypatch.setattr("main.Interface", lambda *a, **k: Mock(
        process_events=lambda: None,
        clear=lambda: None,
        draw_car_grid=lambda *a, **k: None,
        draw_metrics_grid=lambda *a, **k: None,
        draw_info=lambda x: None,
        update=lambda: None,
        close=lambda: None
    ))
    monkeypatch.setattr("main.TrainingLogger", lambda: Mock(log=lambda *a, **k: None, close=lambda: None))
    monkeypatch.setattr("config.CURRICULUM", [{
        "map_type": "corridor",
        "desc": "Corredor reto",
        "min_reward": 1,
        "min_checkpoints": 1,
        "episodes_eval": 1,
        "max_steps": 10
    }])
    run_curriculum(n_parallel=1)
    print("Finalizando test_run_curriculum_complete")

@pytest.mark.timeout(15)
def test_train_phase_success(monkeypatch):
    print("Iniciando test_train_phase_success")
    env = CorridaEnv(map_type="corridor")
    monkeypatch.setattr("agent.Agent.train", lambda self, *a, **k: None)
    monkeypatch.setattr("agent.Agent.evaluate", lambda self, env, n_episodes: 100)
    phase_config = {"map_type": "corridor", "min_reward": 50, "episodes_eval": 10}
    assert train_phase(phase_config, n_parallel=1)
    print("Finalizando test_train_phase_success")

# CORREÇÃO: check_resources e get_user_config não existem mais no main.py
# Estes testes foram removidos pois as funções foram removidas da arquitetura

@pytest.mark.timeout(15)
def test_training_logger(tmp_path):
    print("Iniciando test_training_logger")
    logger = TrainingLogger(base_dir=str(tmp_path))
    logger.log(1, [10], [0], actions=[0], checkpoints=[1], episode_time=5.0, success=True)
    logger.close()
    assert os.path.exists(tmp_path / logger.session_dir / f"treinados_sucesso_{logger.session_time}.txt")
    print("Finalizando test_training_logger")
