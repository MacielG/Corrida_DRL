"""Main refatorado - Separação clara de responsabilidades.

Quebrado em 5 funções principais:
1. setup_interface_and_agents() - Inicializa interface + menu de agentes
2. training_loop() - Loop principal de treinamento
3. handle_menu_state() - Lógica de navegação de menus
4. handle_simulation_state() - Lógica de simulação/corrida
5. main() - Coordena tudo
"""
import sys
import time
import pygame
from environment import CorridaEnv, MultiAgentEnv
from agent import Agent
from metrics import Metrics
from interface_dpg import InterfaceDPG as Interface
from config import PHASES, ENV_SCALE, SIM_SPEED, TIME_STEP
import argparse
import psutil
from logger import setup_logger
from interface_agents import AgentInfo, load_agents, save_agents
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
import gc
import os
from datetime import datetime
from config import load_config, CURRICULUM
import numpy as np

logger = setup_logger()

# ============================================================================
# CONSTANTES
# ============================================================================
CPU_LIMIT = 90
SLEEP_TIME = 0.005
MAX_HISTORY = 30  # Limita histórico de agentes


# ============================================================================
# CLASSES AUXILIARES
# ============================================================================
class TrainingLogger:
    """Logger de episódios de treinamento."""
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
        """Registra um episódio."""
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
        """Fecha arquivos de log."""
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


class RaceManager:
     """Gerenciador de corridas multi-agentes com tracking de ranking."""
     def __init__(self, agents_info_list, map_type, n_parallel=8):
         self.agents_info = agents_info_list
         self.map_type = map_type
         self.n_parallel = n_parallel
         self.models = []
         self.agent_stats = []
         self.race_history = []  # Histórico de corridas
         self.scores = {}  # Scores da corrida atual: {agent_name: score}
         
         for agent_info in agents_info_list:
             try:
                 model_path = agent_info.modelo_path.replace(".zip", "")
                 agent_instance = Agent(None, model_path=model_path)
                 if os.path.exists(agent_info.modelo_path):
                     agent_instance.load(agent_info.modelo_path)
                     self.models.append(agent_instance)
                     self.agent_stats.append(agent_info.stats)
                     self.scores[agent_info.nome] = 0.0
                     logger.info(f"[RaceManager] Modelo carregado: {agent_info.nome}")
             except Exception as e:
                 logger.warning(f"[RaceManager] Falha ao carregar {agent_info.nome}: {e}")
         
         if not self.models:
             logger.warning("[RaceManager] Nenhum modelo carregado!")
             self.models = [None]
             self.agent_stats = [{"accel": 0.5, "turn_speed": 5.0, "max_speed": 20.0}]
     
     def get_actions(self, observations):
         """Predições de múltiplos modelos."""
         actions = []
         for i, obs in enumerate(observations):
             model_idx = i % len(self.models)
             try:
                 if self.models[model_idx] is not None:
                     action, _ = self.models[model_idx].predict(np.array([obs]), deterministic=False)
                     actions.append(int(action[0]))
                 else:
                     actions.append(0)
             except Exception as e:
                 logger.warning(f"[RaceManager] Erro na predição: {e}")
                 actions.append(0)
         return actions
     
     def update_score(self, agent_name: str, reward: float) -> None:
         """Atualiza score de um agente."""
         if agent_name in self.scores:
             self.scores[agent_name] += reward
     
     def get_final_ranking(self) -> list:
         """Retorna ranking final de agentes por score.
         
         Returns:
             list: Lista de tuplas (agent_name, score), ordenada por score decrescente.
         """
         ranking = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
         return ranking
     
     def save_race_history(self, filename: str = "race_history.json") -> None:
         """Salva histórico de corridas em arquivo JSON.
         
         Args:
             filename: Caminho do arquivo.
         """
         import json
         try:
             with open(filename, 'w') as f:
                 json.dump({
                     'map_type': self.map_type,
                     'ranking': self.get_final_ranking(),
                     'timestamp': datetime.now().isoformat(),
                     'race_history': self.race_history
                 }, f, indent=2)
             logger.info(f"[RaceManager] Histórico salvo em {filename}")
         except Exception as e:
             logger.error(f"[RaceManager] Falha ao salvar histórico: {e}")
     
     def load_race_history(self, filename: str = "race_history.json") -> None:
         """Carrega histórico de corridas de arquivo JSON.
         
         Args:
             filename: Caminho do arquivo.
         """
         import json
         try:
             with open(filename, 'r') as f:
                 data = json.load(f)
                 self.race_history = data.get('race_history', [])
             logger.info(f"[RaceManager] Histórico carregado de {filename}")
         except Exception as e:
             logger.warning(f"[RaceManager] Falha ao carregar histórico: {e}")


def check_resources():
    """Verifica uso de memória e CPU."""
    mem = psutil.virtual_memory().percent
    cpu = psutil.cpu_percent(interval=0.05)
    if mem > 80 or cpu > 90:
        time.sleep(0.1)


def make_env(map_type, car_stats=None):
    """Factory function para criar ambientes."""
    return lambda: CorridaEnv(map_type=map_type, car_stats=car_stats)


# ============================================================================
# FUNÇÃO 1: SETUP INTERFACE & AGENTES (70 linhas)
# ============================================================================
def setup_interface_and_agents(fase_desc, n_parallel):
    """Inicializa interface e carrega agentes.
    
    Returns:
        interface, selected_agent, selected_map
    """
    interface = Interface(width=800, height=600, fase_desc=fase_desc, n_parallel=n_parallel)
    interface.state = "menu_inicial"
    
    # Menu loop
    while interface.state != "simulacao":
        interface.update()
        
        if interface.state == "menu_inicial":
            interface.menu.draw_menu_inicial(interface.screen)
            idx = interface.menu.handle_menu_events(interface.state, interface.menu.menu_btns)
            if idx == 0:
                interface.change_state("selecao_agente")
            elif idx == 1:
                interface.change_state("selecao_agente")
            elif idx == 2:
                interface.change_state("ranking")
            elif idx == 3:
                pygame.quit()
                exit()
            elif idx == 4:
                interface.change_state("gestao_agentes")
            interface.clock.tick(60)
        
        elif interface.state == "selecao_agente":
            agents_check = load_agents()
            if not agents_check:
                interface.change_state("gestao_agentes")
            else:
                interface.select_screen.draw_selecao_agente(interface.screen, 
                                                           selected_agent=interface.selected_agent,
                                                           selected_map=interface.selected_map)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mx, my = pygame.mouse.get_pos()
                        for ag, rect in interface.select_screen.agente_btns:
                            if pygame.Rect(rect).collidepoint(mx, my):
                                interface.selected_agent = ag
                                interface.change_state("selecao_mapa")
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        interface.change_state("menu_inicial")
            interface.clock.tick(60)
        
        elif interface.state == "selecao_mapa":
            interface.select_screen.draw_selecao_mapa(interface.screen, selected_map=interface.selected_map)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    for mp, rect in interface.select_screen.mapa_btns:
                        if pygame.Rect(rect).collidepoint(mx, my):
                            interface.selected_map = mp
                            interface.change_state("simulacao")
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    interface.change_state("selecao_agente")
            interface.clock.tick(60)
        
        elif interface.state == "ranking":
            agents_loaded = [AgentInfo.from_dict(a).to_dict() for a in load_agents()]
            interface.ranking_screen.draw_ranking(interface.screen, agents_data=agents_loaded)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    interface.change_state("menu_inicial")
            interface.clock.tick(60)
        
        elif interface.state == "gestao_agentes":
            from interface_agents import (draw_gestao_agentes, handle_gestao_agentes_events)
            agents = load_agents()
            gestao_btn_novo, gestao_agent_cards, gestao_back_btn = [], [], []
            draw_gestao_agentes(interface.screen, interface.width, interface.height, 
                               agents, gestao_btn_novo, gestao_agent_cards, gestao_back_btn)
            result = handle_gestao_agentes_events(pygame.event.get(), gestao_btn_novo, 
                                                 gestao_agent_cards, agents, gestao_back_btn, interface)
            if result == "back":
                interface.change_state("menu_inicial")
            interface.clock.tick(60)
    
    # Busca agente selecionado
    agents = [AgentInfo.from_dict(a) for a in load_agents()]
    agent_info = next((a for a in agents if a.nome == interface.selected_agent), None)
    if not agent_info:
        logger.error("Agente não encontrado!")
        return None, None, None
    
    selected_map = interface.selected_map or "corridor"
    logger.info(f"Agente: {agent_info.nome} | Mapa: {selected_map}")
    
    return interface, agent_info, selected_map


# ============================================================================
# FUNÇÃO 2: TRAINING LOOP (200 linhas)
# ============================================================================
def training_loop(interface, agent_info, selected_map, agent, env, n_parallel, race_manager=None):
    """Loop principal de treinamento.
    
    Args:
        interface: Interface gráfica
        agent_info: AgentInfo do agente selecionado
        selected_map: Mapa selecionado
        agent: Agent treinável (None se race_manager está ativo)
        env: Ambiente vetorizado
        n_parallel: Número de ambientes paralelos
        race_manager: RaceManager ou None
    """
    training_logger = TrainingLogger()
    
    # Carrega ranking
    try:
        interface.load_ranking_data()
    except FileNotFoundError:
        interface.ranking_data = {}
    
    # Cache de agentes
    agents_current = [AgentInfo.from_dict(a) for a in load_agents()]
    agent_info_cache = next((a for a in agents_current if a.nome == interface.selected_agent), None)
    
    logger.info(f"Iniciando treinamento em {n_parallel} ambientes paralelos")
    
    # Inicializa históricos
    obs, _ = env.reset()
    rewards_hist = [[] for _ in range(n_parallel)]
    collisions_hist = [[] for _ in range(n_parallel)]
    penalties_hist = [[] for _ in range(n_parallel)]
    actions_hist = [[] for _ in range(n_parallel)]
    checkpoints_hist = [[] for _ in range(n_parallel)]
    episodios = [0 for _ in range(n_parallel)]
    trajs = [[(obs[i][0], obs[i][1])] for i in range(n_parallel)]
    dones = [False for _ in range(n_parallel)]
    ciclo_total = 0
    iter_count = 0
    
    # Loop principal
    while True:
        # Check resources a cada 100 iterações
        if iter_count % 100 == 0:
            check_resources()
        
        interface.process_events()
        
        # Pausa
        if interface.paused:
            interface.draw_dashboard(rewards_hist, collisions_hist, penalties_hist, 
                                    ciclo_total, 0, 0)
            interface.update()
            time.sleep(0.05)
            continue
        
        # Renderiza
        interface.clear()
        for idx, env_single in enumerate(env.envs):
            interface.draw_env_grid_simple(env_single, idx)
        
        # Predição de ações
        if race_manager:
            actions = race_manager.get_actions(obs)
        else:
            actions_array, _ = agent.model.predict(obs, deterministic=False)
            actions = [int(a) for a in actions_array]
        
        # Step no ambiente
        obs_, rewards, dones, infos = env.step(actions)
        obs = obs_
        
        # Atualiza históricos
        speeds = []
        unique_states = set()
        for idx in range(n_parallel):
            penalty = min(0, rewards[idx])
            rewards_hist[idx].append(rewards[idx])
            collisions_hist[idx].append(infos[idx].get("collisions", 0))
            penalties_hist[idx].append(penalty)
            actions_hist[idx].append(int(actions[idx]))
            checkpoints_hist[idx].append(infos[idx].get("checkpoint", 0))
            speeds.append(abs(obs[idx][2]*2))
            unique_states.add((round(obs[idx][0],1), round(obs[idx][1],1), round(obs[idx][3],1)))
        
        ciclo_total += sum([1 for d in dones if d])
        avg_speed = sum(speeds)/len(speeds) if speeds else 0.0
        n_dif = len(unique_states)
        
        # Desenha dashboard
        interface.draw_dashboard(rewards_hist, collisions_hist, penalties_hist, 
                                ciclo_total, avg_speed, n_dif)
        interface.update()
        iter_count += 1
        time.sleep(0.05)
        
        # Log a cada 20 episódios
        if iter_count % 20 == 0:
            avg_reward = sum([sum(r[-20:]) for r in rewards_hist]) / (20 * n_parallel)
            logger.info(f"Episódio {ciclo_total} | Média recompensa: {avg_reward:.2f}")
        
        # Processa finais de episódios
        for idx in range(n_parallel):
            if dones[idx]:
                is_success = infos[idx].get('success', False)
                episode_time = infos[idx].get('episode_time', 0)
                training_logger.log(idx, rewards_hist[idx], collisions_hist[idx], 
                                  actions=actions_hist[idx], checkpoints=checkpoints_hist[idx], 
                                  episode_time=episode_time, success=is_success)
                
                # Atualiza ranking
                key = f"{agent_info.tipo}|{selected_map}"
                score = sum(rewards_hist[idx])
                prev = interface.ranking_data.get(key, {"score": -float('inf')})
                if score > prev["score"]:
                    interface.ranking_data[key] = {"score": score, "speed": avg_speed, "tempo": episode_time}
                    interface.save_ranking_data()
                
                # Atualiza agente
                if agent_info_cache:
                    agent_info_cache.tempo_acumulado += episode_time
                    xp_gained = max(0, int(score * 10))
                    agent_info_cache.historico.append({
                        "mapa": selected_map,
                        "score": score,
                        "velocidade": avg_speed,
                        "tempo": episode_time,
                        "xp_gained": xp_gained,
                        "checkpoints": checkpoints_hist[idx][-1] if checkpoints_hist[idx] else 0,
                        "data": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "tipo_evento": "simulacao"
                    })
                    agent_info_cache.historico = agent_info_cache.historico[-MAX_HISTORY:]
                    
                    # Salva
                    agents_all = [AgentInfo.from_dict(a) for a in load_agents()]
                    agents_all = [a.to_dict() if a.nome != agent_info_cache.nome else agent_info_cache.to_dict() for a in agents_all]
                    save_agents(agents_all)
                
                # Reset
                obs_single, _ = env.envs[idx].reset()
                obs[idx] = obs_single
                dones[idx] = False
                episodios[idx] += 1
                actions_hist[idx] = []
                checkpoints_hist[idx] = []
                gc.collect()
        
        # Check restart
        if interface.should_restart():
            obs, _ = env.reset()
            for idx in range(n_parallel):
                rewards_hist[idx] = []
                collisions_hist[idx] = []
                penalties_hist[idx] = []
                actions_hist[idx] = []
                checkpoints_hist[idx] = []
            ciclo_total = 0
            iter_count = 0
            interface.clear_restart()
    
    training_logger.close()


# ============================================================================
# FUNÇÃO 3: MAIN ORQUESTRADOR (40 linhas)
# ============================================================================
def main(map_type="corridor", car_to_train=1, fase_idx=0, n_parallel=8, 
         skip_training=False, learning_rate=None, gamma=None):
    """Coordena fluxo principal."""
    from config import PHASES
    fase_desc = PHASES[fase_idx]["desc"] if fase_idx < len(PHASES) else map_type
    
    # 1. Setup interface e agentes
    result = setup_interface_and_agents(fase_desc, n_parallel)
    if result[0] is None:
        return
    interface, agent_info, selected_map = result
    
    # Progress bar
    for i in range(10, 101, 10):
        interface.draw_loading(f'Renderizando agentes... ({i}%)', progresso=i/100, animar=False)
        interface.process_events()
        time.sleep(0.05)
    
    interface.draw_loading('Agentes renderizados! Treinamento iniciado.', progresso=1.0, animar=False)
    interface.update()
    print('Iniciando treinamento...')
    time.sleep(1)
    
    # 2. Prepara ambiente e agente
    os.environ["RL_ALGORITHM"] = agent_info.tipo
    
    if not skip_training:
        # Modo treino
        logger.info("[MODO] Treino com um agente")
        env = DummyVecEnv([make_env(selected_map, car_stats=agent_info.stats) 
                          for _ in range(n_parallel)])
        model_path = f"models/model_{selected_map}_{agent_info.tipo}"
        agent = Agent(env, model_path=model_path, learning_rate=learning_rate, gamma=gamma)
        model_file = model_path + "_step_10000.zip"
        if os.path.exists(model_file):
            agent.load(model_file)
            logger.info(f"Loaded pre-trained model from {model_file}")
        race_manager = None
    else:
        # Modo corrida
        logger.info("[MODO] Corrida Competitiva")
        all_agents = [AgentInfo.from_dict(a) for a in load_agents()]
        rivals = [a for a in all_agents if a.nome != agent_info.nome]
        race_agents = [agent_info] + rivals[:n_parallel-1]
        while len(race_agents) < n_parallel:
            race_agents.append(agent_info)
        
        env = DummyVecEnv([make_env(selected_map, car_stats=ag.stats) for ag in race_agents])
        race_manager = RaceManager(race_agents, selected_map, n_parallel)
        agent = None
    
    # 3. Loop principal
    training_loop(interface, agent_info, selected_map, agent, env, n_parallel, race_manager)


# ============================================================================
# CURRICULUM TRAINING
# ============================================================================
def run_curriculum(car_to_train=1, n_parallel=4):
    """Executa currículo de treinamento."""
    for etapa_idx, etapa in enumerate(CURRICULUM):
        logger.info(f"\n=== Etapa {etapa_idx+1}: {etapa['desc']} ===")
        env = DummyVecEnv([lambda: CorridaEnv(map_type=etapa["map_type"]) 
                          for _ in range(n_parallel)])
        agent = Agent(env, model_path=f"models/model_{etapa['map_type']}_car{car_to_train}")
        interface = Interface(width=env.envs[0].width, height=env.envs[0].height, 
                            fase_desc=etapa["desc"], n_parallel=n_parallel)
        training_logger = TrainingLogger()
        
        episodes_eval = etapa.get("episodes_eval", 10)
        min_reward = etapa.get("min_reward", 0)
        min_checkpoints = etapa.get("min_checkpoints", 0)
        
        episode_rewards = [[] for _ in range(n_parallel)]
        episode_checkpoints = [[] for _ in range(n_parallel)]
        states, _ = env.reset()
        dones = [False for _ in range(n_parallel)]
        episodes_completed = [0 for _ in range(n_parallel)]
        rewards_temp = [[] for _ in range(n_parallel)]
        current_checkpoints = [0 for _ in range(n_parallel)]
        
        while True:
            interface.process_events()
            interface.clear()
            
            actions_array, _ = agent.model.predict(states, deterministic=False)
            actions = [int(a) for a in actions_array]
            obs_, rewards, dones, infos = env.step(actions)
            
            for idx in range(n_parallel):
                if not dones[idx]:
                    rewards_temp[idx].append(rewards[idx])
                    if infos[idx].get("success", False):
                        current_checkpoints[idx] += 1
                    states[idx] = obs_[idx]
                interface.draw_car_grid(env.envs[idx].car1_pos, env.envs[idx].car1_angle, idx)
            
            interface.dashboard.draw_metrics_grid(rewards_temp, [], [])
            interface.dashboard.draw_info(0)
            interface.update()
            
            for i in range(n_parallel):
                if dones[i]:
                    episode_rewards[i].append(sum(rewards_temp[i]))
                    episode_checkpoints[i].append(current_checkpoints[i])
                    rewards_temp[i] = []
                    current_checkpoints[i] = 0
                    training_logger.log(i, [episode_rewards[i][-1]] if episode_rewards[i] else [0], [],
                                      actions=None, checkpoints=[episode_checkpoints[i][-1]] if episode_checkpoints[i] else [0],
                                      episode_time=None, success=True)
                    obs_reset, _ = env.envs[i].reset()
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
    """Treina uma fase específica."""
    from environment import CorridaEnv
    from agent import Agent
    env = CorridaEnv(map_type=phase_config["map_type"])
    env.max_steps = phase_config.get("max_steps", 500)
    agent = Agent(env)
    for epoch in range(100):
        agent.train(total_timesteps=10000)
        score = agent.evaluate(env, n_episodes=phase_config.get("episodes_eval", 20))
        if score >= phase_config["min_reward"]:
            return True
    return False


# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Corrida DRL Training")
    parser.add_argument("--skip-training", action="store_true", help="Skip training and load pre-trained model")
    parser.add_argument("--learning_rate", type=float, default=None, help="Taxa de aprendizado")
    parser.add_argument("--gamma", type=float, default=None, help="Fator de desconto RL")
    parser.add_argument("--n_parallel", type=int, default=None, help="Execuções paralelas")
    parser.add_argument("--map_type", type=str, default=None, help="Tipo de mapa")
    parser.add_argument("--config", type=str, default="config.json", help="Arquivo JSON de config")
    args = parser.parse_args()
    
    cfg = load_config(args.config)
    if args.learning_rate is not None:
        cfg["learning_rate"] = args.learning_rate
    if args.gamma is not None:
        cfg["gamma"] = args.gamma
    if args.n_parallel is not None:
        cfg["n_parallel"] = args.n_parallel
    if args.map_type is not None:
        cfg["map_type"] = args.map_type
    
    map_type, fase_idx, n_agents, car_to_train, n_parallel = \
        cfg["map_type"], 0, 1, 1, cfg["n_parallel"]
    
    main(map_type=map_type, car_to_train=car_to_train, fase_idx=fase_idx, 
         n_parallel=n_parallel, skip_training=args.skip_training, 
         learning_rate=cfg["learning_rate"], gamma=cfg["gamma"])
    run_curriculum(car_to_train=car_to_train, n_parallel=n_parallel)
