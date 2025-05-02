import pytest
import os
from main import main, run_curriculum, train_phase, check_resources, get_user_config, TrainingLogger
from environment import CorridaEnv
from unittest.mock import Mock
import psutil

class StopTestLoop(Exception):
    pass

@pytest.mark.timeout(15)
def test_main_loop_pause(monkeypatch):
    print("Iniciando test_main_loop_pause")
    env = Mock(spec=CorridaEnv, width=800, height=600)
    print("Mock CorridaEnv criado")
    env.reset.return_value = ([0] * 15, {})
    env.step.return_value = ([0] * 15, 0.0, False, False, {})
    print("Mock reset e step configurados")
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
        def draw_env_grid(self, env_single, idx):
            print(f"draw_env_grid chamado para idx={idx}")
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

@pytest.mark.timeout(15)
def test_run_curriculum_complete(monkeypatch):
    print("Iniciando test_run_curriculum_complete")
    env = Mock(spec=CorridaEnv, width=800, height=600)
    env.reset.return_value = ([0] * 15, {})
    env.step.return_value = ([0] * 15, 100, True, False, {"success": True, "checkpoint": 2})
    # Configura DummyVecEnv para retornar uma lista de estados
    mock_vec_env = Mock()
    mock_vec_env.envs = [env]
    mock_vec_env.reset.return_value = [[0] * 15]
    mock_vec_env.step.return_value = ([[0] * 15], [100], [True], [False], [{"success": True, "checkpoint": 2}])
    monkeypatch.setattr("main.DummyVecEnv", lambda x: mock_vec_env)
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

@pytest.mark.timeout(15)
def test_check_resources_high_usage(monkeypatch):
    print("Iniciando test_check_resources_high_usage")
    monkeypatch.setattr(psutil, "virtual_memory", lambda: Mock(percent=85))
    monkeypatch.setattr(psutil, "cpu_percent", lambda interval: 95)
    monkeypatch.setattr("time.sleep", Mock())
    check_resources()
    assert psutil.time.sleep.called
    print("Finalizando test_check_resources_high_usage")

@pytest.mark.timeout(15)
def test_get_user_config(monkeypatch):
    print("Iniciando test_get_user_config")
    monkeypatch.setattr("builtins.input", lambda x: "0")
    map_type, fase_idx, n_agents, car_to_train, n_parallel = get_user_config()
    assert map_type == "corridor"
    assert fase_idx == 0
    print("Finalizando test_get_user_config")

@pytest.mark.timeout(15)
def test_training_logger(tmp_path):
    print("Iniciando test_training_logger")
    logger = TrainingLogger(base_dir=str(tmp_path))
    logger.log(1, [10], [0], actions=[0], checkpoints=[1], episode_time=5.0, success=True)
    logger.close()
    assert os.path.exists(tmp_path / logger.session_dir / f"treinados_sucesso_{logger.session_time}.txt")
    print("Finalizando test_training_logger")
