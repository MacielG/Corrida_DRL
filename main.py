"""Main do projeto Corrida DRL, com suporte a fases, escala, tempo e métricas pedagógicas.

Gerencia o ciclo de treinamento, avaliação, logging e interface gráfica do agente RL.
"""
import sys
from environment import CorridaEnv, MultiAgentEnv
from agent import Agent
from metrics import Metrics
from interface import Interface
from config import PHASES, ENV_SCALE, SIM_SPEED, TIME_STEP
import argparse
import time
import psutil
import math
import os
from datetime import datetime
from logger import setup_logger
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
import gc
import json
from config import load_config

CPU_LIMIT = 90  # porcentagem máxima de uso de CPU permitida
SLEEP_TIME = 0.005  # segundos para dormir se passar do limite

def check_resources():
    """Verifica uso de memória e CPU, pausando se necessário."""
    mem = psutil.virtual_memory().percent
    cpu = psutil.cpu_percent(interval=0.05)
    if mem > 80 or cpu > 90:
        time.sleep(0.1)

class TrainingLogger:
    """Logger de episódios de treinamento, salva métricas em arquivos.

    Args:
        base_dir (str): Diretório base para logs.
    """
    def __init__(self, base_dir="logs"):
        os.makedirs(base_dir, exist_ok=True)
        now = datetime.now()
        now_str = now.strftime("%Y%m%d_%H%M%S")
        hora_str = now.strftime("hora-%H-%M-%S")
        self.session_time = now_str
        self.session_dir = os.path.join(base_dir, f"sessao_{now_str}_{hora_str}")
        os.makedirs(self.session_dir, exist_ok=True)
        self.success_file = os.path.join(self.session_dir, f"treinados_sucesso_{now_str}.txt")
        self.incomplete_file = os.path.join(self.session_dir, f"incompletos_{now_str}.txt")
        self.success_log = open(self.success_file, "a", encoding="utf-8")
        self.incomplete_log = open(self.incomplete_file, "a", encoding="utf-8")
        self.start_mem = psutil.virtual_memory().percent
        self.start_cpu = psutil.cpu_percent(interval=0.05)

    def log(self, ep_idx, rewards, collisions, actions=None, checkpoints=None, episode_time=None, success=True):
        """Registra um episódio no arquivo de log.

        Args:
            ep_idx (int): Índice do episódio.
            rewards (list): Lista de recompensas.
            collisions (list): Lista de colisões.
            actions (list): Lista de ações.
            checkpoints (list): Lista de checkpoints.
            episode_time (float): Tempo do episódio.
            success (bool): Se o episódio foi bem-sucedido.
        """
        log_file = self.success_log if success else self.incomplete_log
        log_file.write(f"Episódio {ep_idx}:\n")
        log_file.write(f"Recompensas: {rewards}\n")
        log_file.write(f"Colisões: {collisions}\n")
        if actions is not None:
            log_file.write(f"Ações: {actions}\n")
        if checkpoints is not None:
            log_file.write(f"Checkpoints: {checkpoints}\n")
        if episode_time is not None:
            log_file.write(f"Tempo do episódio: {episode_time:.2f}s\n")
        log_file.write(f"Sucesso: {success}\n")
        log_file.write("-"*40+"\n")
        log_file.flush()

    def close(self):
        """Fecha os arquivos de log da sessão."""
        self.success_log.write(f"Sessão iniciada em: {self.session_time}\n")
        self.incomplete_log.write(f"Sessão iniciada em: {self.session_time}\n")
        end_mem = psutil.virtual_memory().percent
        end_cpu = psutil.cpu_percent(interval=0.05)
        self.success_log.write(f"Memória inicial: {self.start_mem:.1f}% | Memória final: {end_mem:.1f}%\n")
        self.success_log.write(f"CPU inicial: {self.start_cpu:.1f}% | CPU final: {end_cpu:.1f}%\n")
        self.incomplete_log.write(f"Memória inicial: {self.start_mem:.1f}% | Memória final: {end_mem:.1f}%\n")
        self.incomplete_log.write(f"CPU inicial: {self.start_cpu:.1f}% | CPU final: {end_cpu:.1f}%\n")
        self.success_log.close()
        self.incomplete_log.close()

import os
import argparse

logger = setup_logger()

def make_env(map_type):
    return lambda: CorridaEnv(map_type=map_type)

def update_curriculum(current_performance: float):
    from config import PHASES
    difficulty_level = min(int(current_performance / 50), len(PHASES)-1)
    return PHASES[difficulty_level]

def main(map_type="corridor", car_to_train=1, fase_idx=0, n_parallel=8, skip_training=False, learning_rate=None, gamma=None):
    """Função principal de execução do treinamento e avaliação.

    Args:
        map_type (str): Tipo de mapa.
        car_to_train (int): Carro a ser treinado.
        fase_idx (int): Índice da fase.
        n_parallel (int): Execuções paralelas.
        skip_training (bool): Se True, apenas avalia modelo pré-treinado.
        learning_rate (float): Taxa de aprendizado do agente RL.
        gamma (float): Fator de desconto RL.
    """
    from config import PHASES
    fase_desc = PHASES[fase_idx]["desc"] if fase_idx < len(PHASES) else map_type
    # Usa SubprocVecEnv para paralelismo real
    env = SubprocVecEnv([make_env(map_type) for _ in range(n_parallel)])
    model_path = f"models/model_{map_type}_car{car_to_train}"
    agent = Agent(env, model_path=model_path, learning_rate=learning_rate, gamma=gamma)
    if not skip_training:
        model_file = model_path + "_step_10000.zip"
        if os.path.exists(model_file):
            agent.load(model_file)
            logger.info(f"Loaded pre-trained model from {model_file}")
        else:
            logger.info("Training agent from scratch...")
            agent.train(total_timesteps=10000)
    else:
        model_file = model_path + "_step_10000.zip"
        if os.path.exists(model_file):
            agent.load(model_file)
            logger.info(f"Loaded pre-trained model from {model_file}")
        else:
            logger.info("No pre-trained model found, skipping training as requested.")
    interface = Interface(width=env.envs[0].width, height=env.envs[0].height, fase_desc=fase_desc, n_parallel=n_parallel)
    training_logger = TrainingLogger()
    logger.info(f"Treinando {n_parallel} execuções paralelas do agente {car_to_train} no mapa: {map_type} (Fase: {fase_desc})")
    obs, info = env.reset()
    rewards_hist = [[] for _ in range(n_parallel)]
    collisions_hist = [[] for _ in range(n_parallel)]
    penalties_hist = [[] for _ in range(n_parallel)]
    actions_hist = [[] for _ in range(n_parallel)]
    checkpoints_hist = [[] for _ in range(n_parallel)]
    episodios = [0 for _ in range(n_parallel)]
    ciclo_total = 0
    trajs = [[(obs[i][0], obs[i][1])] for i in range(n_parallel)]
    iter_count = 0
    dones = [False for _ in range(n_parallel)]
    avg_speed = 0.0  # Corrige UnboundLocalError
    n_dif = 0        # Corrige UnboundLocalError
    while True:
        if iter_count % 100 == 0:
            check_resources()
        interface.process_events()
        if interface.paused:
            interface.draw_dashboard(rewards_hist, collisions_hist, penalties_hist, ciclo_total, avg_speed, n_dif)
            interface.update()
            time.sleep(0.05)
            continue
        interface.clear()
        # Desenha cada ambiente paralelo em um grid
        for idx, env_single in enumerate(env.envs):
            interface.draw_env_grid(env_single, idx)
        speeds = []
        unique_states = set()
        actions = [int(agent.predict(obs[i])) for i in range(n_parallel)]  # Garante int
        step_result = env.step(actions)
        if len(step_result) == 5:
            obs_, rewards, terminateds, truncateds, infos = step_result
        else:
            obs_, rewards, dones, infos = step_result
            terminateds = dones
            truncateds = [False for _ in dones]
        dones = [terminateds[i] or truncateds[i] for i in range(n_parallel)]
        obs = obs_
        for idx in range(n_parallel):
            penalty = min(0, rewards[idx])
            rewards_hist[idx].append(rewards[idx])
            collisions_hist[idx].append(infos[idx]["collisions"] if "collisions" in infos[idx] else 0)
            penalties_hist[idx].append(penalty)
            # Corrige: salva ações como int
            actions_hist[idx].append(int(actions[idx]))
            checkpoints_hist[idx].append(infos[idx].get("checkpoint", 0))
            # Desnormaliza velocidade
            speeds.append(abs(obs[idx][2]*2))
            unique_states.add((round(obs[idx][0],1), round(obs[idx][1],1), round(obs[idx][3],1)))
        ciclo_total += sum([1 for d in dones if d])
        avg_speed = sum(speeds)/len(speeds) if speeds else 0.0
        n_dif = len(unique_states)
        interface.draw_dashboard(rewards_hist, collisions_hist, penalties_hist, ciclo_total, avg_speed, n_dif)
        interface.update()
        iter_count += 1
        time.sleep(0.05)
        for idx in range(n_parallel):
            if dones[idx]:
                is_success = infos[idx].get('success', False)
                episode_time = infos[idx].get('episode_time', None)
                training_logger.log(idx, rewards_hist[idx], collisions_hist[idx], actions=actions_hist[idx], checkpoints=checkpoints_hist[idx], episode_time=episode_time, success=is_success)
                obs_single = env.envs[idx].reset()
                # Corrige: sempre pega apenas o vetor de observação
                if isinstance(obs_single, tuple):
                    obs[idx] = obs_single[0]
                else:
                    obs[idx] = obs_single
                dones[idx] = False
                episodios[idx] += 1
                actions_hist[idx] = []
                checkpoints_hist[idx] = []
                gc.collect()
        if interface.should_restart():
            obs = env.reset()
            for idx in range(n_parallel):
                rewards_hist[idx] = []
                collisions_hist[idx] = []
                penalties_hist[idx] = []
                actions_hist[idx] = []
                checkpoints_hist[idx] = []
            ciclo_total = 0
            iter_count = 0
            interface.clear_restart()
    # Garante fechamento do logger
    training_logger.close()

def run_curriculum(car_to_train=1, n_parallel=4):
    """Executa o currículo de fases para o agente RL.

    Args:
        car_to_train (int): Carro a ser treinado.
        n_parallel (int): Execuções paralelas.
    """
    from config import CURRICULUM
    for etapa_idx, etapa in enumerate(CURRICULUM):
        logger.info(f"\n=== Etapa {etapa_idx+1}: {etapa['desc']} ===")
        # Corrigido: usar DummyVecEnv para paralelismo real
        env = DummyVecEnv([lambda: CorridaEnv(map_type=etapa["map_type"]) for _ in range(n_parallel)])
        agent = Agent(env, model_path=f"models/model_{etapa['map_type']}_car{car_to_train}")
        metrics_list = [Metrics() for _ in range(n_parallel)]
        interface = Interface(width=env.envs[0].width, height=env.envs[0].height, fase_desc=etapa["desc"], n_parallel=n_parallel)
        training_logger = TrainingLogger()
        episodes_eval = etapa.get("episodes_eval", 10)
        min_reward = etapa.get("min_reward", 0)
        min_checkpoints = etapa.get("min_checkpoints", 0)
        episode_rewards = [[] for _ in range(n_parallel)]
        episode_checkpoints = [[] for _ in range(n_parallel)]
        states = env.reset()
        dones = [False for _ in range(n_parallel)]
        episodes_completed = [0 for _ in range(n_parallel)]
        rewards_temp = [[] for _ in range(n_parallel)]
        current_checkpoints = [0 for _ in range(n_parallel)]
        while True:
            interface.process_events()
            interface.clear()
            actions = [int(agent.predict(states[i][0] if isinstance(states[i], tuple) else states[i])) for i in range(n_parallel)]
            step_result = env.step(actions)
            if len(step_result) == 5:
                obs_, rewards, terminateds, truncateds, infos = step_result
            else:
                obs_, rewards, dones, infos = step_result
                terminateds = dones
                truncateds = [False for _ in dones]
            dones = [terminateds[i] or truncateds[i] for i in range(n_parallel)]
            for idx in range(n_parallel):
                if not dones[idx]:
                    rewards_temp[idx].append(rewards[idx])
                    if infos[idx].get("success", False):
                        current_checkpoints[idx] += 1
                    states[idx] = obs_[idx]
                interface.draw_car_grid(env.envs[idx].car1_pos, env.envs[idx].car1_angle, idx)
            interface.draw_metrics_grid([sum(r) for r in rewards_temp], current_checkpoints)
            interface.draw_info(0.0)
            interface.update()
            for i in range(n_parallel):
                if dones[i]:
                    episode_rewards[i].append(sum(rewards_temp[i]))
                    episode_checkpoints[i].append(current_checkpoints[i])
                    rewards_temp[i] = []
                    current_checkpoints[i] = 0
                    # Chamada ao logger para garantir registro do episódio
                    training_logger.log(
                        i,
                        episode_rewards[i][-1] if episode_rewards[i] else [],
                        [],  # colisões não são registradas aqui
                        actions=None,
                        checkpoints=episode_checkpoints[i][-1] if episode_checkpoints[i] else [],
                        episode_time=None,
                        success=True
                    )
                    obs_reset = env.envs[i].reset()
                    if isinstance(obs_reset, tuple):
                        states[i] = obs_reset[0]
                    else:
                        states[i] = obs_reset
                    dones[i] = False
                    episodes_completed[i] += 1
            total_episodes = sum(episodes_completed)
            if total_episodes >= episodes_eval * n_parallel:
                avg_reward = sum([sum(r[-episodes_eval:]) for r in episode_rewards]) / (episodes_eval * n_parallel)
                avg_checkpoints = sum([sum(c[-episodes_eval:]) for c in episode_checkpoints]) / (episodes_eval * n_parallel)
                if avg_reward >= min_reward and avg_checkpoints >= min_checkpoints:
                    break
        interface.close()
        training_logger.close()

def train_phase(phase_config, n_parallel=4):
    """Treina o agente em uma fase específica do currículo.

    Args:
        phase_config (dict): Configuração da fase.
        n_parallel (int): Execuções paralelas.
    Returns:
        bool: True se atingiu desempenho mínimo.
    """
    from environment import CorridaEnv
    from agent import Agent
    env = CorridaEnv(map_type=phase_config["map_type"])
    env.max_steps = phase_config.get("max_steps", 500)
    agent = Agent(env)
    for epoch in range(100):  # Número máximo de épocas
        agent.train(total_timesteps=10000)
        score = agent.evaluate(env, n_episodes=phase_config.get("episodes_eval", 20))
        if score >= phase_config["min_reward"]:
            return True
    return False

def get_user_config():
    """Solicita configuração do usuário via input.

    Returns:
        tuple: (map_type, fase_idx, n_agents, car_to_train, n_parallel)
    """
    fases = [f["map_type"] for f in PHASES]
    fase_idx = int(input(f"Escolha o mapa/fase (0-{len(fases)-1}): ") or 0)
    map_type = fases[fase_idx]

    n_agents = 1  # Sempre 1 agente
    car_to_train = 1  # Sempre carro 1
    n_parallel = 1  # Sempre 1 execução paralela

    return map_type, fase_idx, n_agents, car_to_train, n_parallel

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Corrida DRL Training")
    parser.add_argument("--skip-training", action="store_true", help="Skip training and load pre-trained model if available")
    parser.add_argument("--learning_rate", type=float, default=None, help="Taxa de aprendizado do agente RL")
    parser.add_argument("--gamma", type=float, default=None, help="Fator de desconto RL")
    parser.add_argument("--n_parallel", type=int, default=None, help="Número de execuções paralelas")
    parser.add_argument("--map_type", type=str, default=None, help="Tipo de mapa (corridor, curve, circle)")
    parser.add_argument("--config", type=str, default="config.json", help="Arquivo JSON de configuração de hiperparâmetros")
    args = parser.parse_args()

    # Carrega config.json e mescla com argumentos
    cfg = load_config(args.config)
    if args.learning_rate is not None:
        cfg["learning_rate"] = args.learning_rate
    if args.gamma is not None:
        cfg["gamma"] = args.gamma
    if args.n_parallel is not None:
        cfg["n_parallel"] = args.n_parallel
    if args.map_type is not None:
        cfg["map_type"] = args.map_type

    map_type, fase_idx, n_agents, car_to_train, n_parallel = cfg["map_type"], 0, 1, 1, cfg["n_parallel"]
    main(map_type=map_type, car_to_train=car_to_train, fase_idx=fase_idx, n_parallel=n_parallel, skip_training=args.skip_training, learning_rate=cfg["learning_rate"], gamma=cfg["gamma"])
    run_curriculum(car_to_train=car_to_train, n_parallel=n_parallel)
