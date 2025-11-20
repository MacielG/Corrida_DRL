"""Main do projeto Corrida DRL, com suporte a fases, escala, tempo e métricas pedagógicas.

Gerencia o ciclo de treinamento, avaliação, logging e interface gráfica do agente RL.
"""
import sys
from environment import CorridaEnv, MultiAgentEnv
from agent import Agent
from metrics import Metrics
from interface_dpg import InterfaceDPG as Interface
from config import PHASES, ENV_SCALE, SIM_SPEED, TIME_STEP
import argparse
import time
import psutil
import math
import os
from datetime import datetime
from logger import setup_logger
import pygame
from interface_agents import AgentInfo, load_agents, save_agents
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

class RaceManager:
    """Gerenciador de corridas multi-modelos para competições de IA.
    
    Permite que múltiplos agentes com diferentes cérebros (PPO, DQN, etc)
    corram simultaneamente no mesmo mapa para criar corridas visuais interessantes.
    """
    def __init__(self, agents_info_list, map_type, n_parallel=8):
        """
        Args:
            agents_info_list (list): Lista de AgentInfo com modelos treinados
            map_type (str): Tipo de mapa ('corridor', 'curve', 'circle')
            n_parallel (int): Número de ambientes paralelos
        """
        self.agents_info = agents_info_list
        self.map_type = map_type
        self.n_parallel = n_parallel
        self.models = []
        self.agent_stats = []
        
        # Carrega todos os modelos
        for agent_info in agents_info_list:
            try:
                # Carrega o modelo específico do agente
                model_path = agent_info.modelo_path.replace(".zip", "")
                agent_instance = Agent(None, model_path=model_path)
                if os.path.exists(agent_info.modelo_path):
                    agent_instance.load(agent_info.modelo_path)
                    self.models.append(agent_instance)
                    self.agent_stats.append(agent_info.stats)
                    logger.info(f"[RaceManager] Modelo carregado: {agent_info.nome}")
            except Exception as e:
                logger.warning(f"[RaceManager] Falha ao carregar {agent_info.nome}: {e}")
        
        if not self.models:
            logger.warning("[RaceManager] Nenhum modelo carregado! Usando modelo padrão.")
            self.models = [None]
            self.agent_stats = [{"accel": 0.5, "turn_speed": 5.0, "max_speed": 20.0}]
    
    def get_actions(self, observations):
        """Predições de múltiplos modelos de forma rotacionada.
        
        Args:
            observations (array): Array de observações [n_parallel, obs_dim]
            
        Returns:
            list: Ações [n_parallel] onde cada índice usa um modelo diferente
        """
        actions = []
        for i, obs in enumerate(observations):
            model_idx = i % len(self.models)
            try:
                if self.models[model_idx] is not None:
                    action, _ = self.models[model_idx].predict(np.array([obs]), deterministic=False)
                    actions.append(int(action[0]))
                else:
                    actions.append(0)  # Ação padrão se modelo não carregou
            except Exception as e:
                logger.warning(f"[RaceManager] Erro na predição do modelo {model_idx}: {e}")
                actions.append(0)
        return actions

def make_env(map_type, car_stats=None):
    """Factory function para criar ambientes com stats customizados."""
    return lambda: CorridaEnv(map_type=map_type, car_stats=car_stats)

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

    # --- NOVO FLUXO: menu visual e gestão de agentes ---
    interface = Interface(width=800, height=600, fase_desc=fase_desc, n_parallel=n_parallel)
    # Adiciona opção de gestão de agentes ao menu
    interface.state = "menu_inicial"

    # Variables for gestao_agentes UI
    gestao_btn_novo = []
    gestao_agent_cards = []
    gestao_back_btn = []

    import pygame
    from interface_agents import (draw_gestao_agentes, handle_gestao_agentes_events,
                                   draw_criar_agente_dialog, handle_criar_agente_events,
                                   draw_editar_agente_dialog, handle_editar_agente_events,
                                   draw_comprar_upgrade_dialog, handle_comprar_upgrade_events)
    agents = [AgentInfo.from_dict(a) for a in load_agents()]

    while True:
        interface.update()  # Garante atualização da interface Dear PyGui
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
                pygame.quit(); exit()
            elif idx == 4:
                interface.change_state("gestao_agentes")
            interface.clock.tick(60)

        elif interface.state == "selecao_agente":
            # Verifica se há agentes criados
            agents_check = load_agents()
            if not agents_check:
                # Sem agentes, redireciona para gestão
                print("[INFO] Nenhum agente criado. Redirecionando para Gestão de Agentes...")
                interface.change_state("gestao_agentes")
                agents = []  # Reinicia lista de agentes
            else:
                interface.select_screen.draw_selecao_agente(interface.screen, selected_agent=interface.selected_agent, selected_map=interface.selected_map)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mx, my = pygame.mouse.get_pos()
                        for ag, rect in interface.select_screen.agente_btns:
                            r = pygame.Rect(rect)
                            if r.collidepoint(mx, my):
                                interface.selected_agent = ag
                                interface.change_state("selecao_mapa")
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        interface.change_state("menu_inicial")
            interface.clock.tick(60)

        elif interface.state == "selecao_mapa":
            interface.select_screen.draw_selecao_mapa(interface.screen, selected_map=interface.selected_map)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    for mp, rect in interface.select_screen.mapa_btns:
                        r = pygame.Rect(rect)
                        if r.collidepoint(mx, my):
                            interface.selected_map = mp
                            interface.change_state("simulacao")
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    interface.change_state("selecao_agente")
            interface.clock.tick(60)

        elif interface.state == "ranking":
            # Carrega dados dos agentes para mostrar stats no ranking
            agents_loaded = [AgentInfo.from_dict(a).to_dict() for a in load_agents()]
            interface.ranking_screen.draw_ranking(interface.screen, agents_data=agents_loaded)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    interface.change_state("menu_inicial")
            interface.clock.tick(60)

        elif interface.state == "gestao_agentes":
            agents = load_agents()  # Recarrega agentes sempre
            draw_gestao_agentes(interface.screen, interface.width, interface.height, agents, gestao_btn_novo, gestao_agent_cards, gestao_back_btn)
            result = handle_gestao_agentes_events(pygame.event.get(), gestao_btn_novo, gestao_agent_cards, agents, gestao_back_btn, interface)
            if result is not None:
                if isinstance(result, tuple) and result[0] == "select":
                    interface.selected_agent = result[1]
                    interface.change_state("menu_inicial")
                elif result == "back":
                    interface.change_state("menu_inicial")
            interface.clock.tick(60)
        
        elif interface.state == "criar_agente":
            agents = load_agents()  # Recarrega agentes
            draw_criar_agente_dialog(interface.screen, interface.width, interface.height,
                                    getattr(interface, 'criar_agente_state', 'GET_NAME'),
                                    getattr(interface, 'criar_agente_nome', ''),
                                    getattr(interface, 'criar_agente_tipo', 0),
                                    getattr(interface, 'criar_agente_error', ''))
            handle_criar_agente_events(pygame.event.get(), agents, interface)
            interface.clock.tick(60)
        
        elif interface.state == "editar_agente":
            agents = load_agents()  # Recarrega agentes
            draw_editar_agente_dialog(interface.screen, interface.width, interface.height,
                                     getattr(interface, 'editar_agente_state', 'GET_NAME'),
                                     getattr(interface, 'editar_agente_ag_original', None),
                                     getattr(interface, 'editar_agente_nome', ''),
                                     getattr(interface, 'editar_agente_tipo', 0),
                                     getattr(interface, 'editar_agente_error', ''))
            handle_editar_agente_events(pygame.event.get(), agents, interface)
            interface.clock.tick(60)
        
        elif interface.state == "comprar_upgrade_agente":
            draw_comprar_upgrade_dialog(interface.screen, interface.width, interface.height,
                                       getattr(interface, 'upgrade_agent_dict', {}),
                                       getattr(interface, 'upgrade_list', []),
                                       getattr(interface, 'upgrade_selected_idx', 0),
                                       getattr(interface, 'upgrade_message', ''))
            handle_comprar_upgrade_events(pygame.event.get(), interface)
            interface.clock.tick(60)

        elif interface.state == "simulacao":
            break
    # Após menu, pega escolhas do usuário
    # Busca agente pelo nome
    agents = [AgentInfo.from_dict(a) for a in load_agents()]
    agent_info = next((a for a in agents if a.nome == interface.selected_agent), None)
    if not agent_info:
        print("Agente não encontrado! Voltando ao menu.")
        return main(map_type, car_to_train, fase_idx, n_parallel, skip_training, learning_rate, gamma)
    selected_agent = agent_info.tipo
    selected_map = interface.selected_map or "corridor"
    print(f"Agente selecionado: {agent_info.nome} ({selected_agent}) | Mapa: {selected_map}")
    print(f"[GAMIFICAÇÃO] Stats do agente: Acel={agent_info.stats['accel']}, Turn={agent_info.stats['turn_speed']}, MaxSpeed={agent_info.stats['max_speed']}")
    print(f"[GAMIFICAÇÃO] Nível do agente: {agent_info.level}")

    # 2. Prepara ambiente, modelo e agente (NÃO treina antes do loop principal)
    from stable_baselines3.common.vec_env import DummyVecEnv
    
    # ===== LÓGICA HÍBRIDA: TREINO vs CORRIDA COMPETITIVA =====
    race_manager = None
    agent = None
    
    if not skip_training:
        # MODO TREINO: 1 agente clonado (como era antes)
        print("[MODO] Treino com um agente")
        env = DummyVecEnv([make_env(selected_map, car_stats=agent_info.stats) for _ in range(n_parallel)])
        
        # Força algoritmo selecionado
        import os
        os.environ["RL_ALGORITHM"] = selected_agent
        model_path = f"models/model_{selected_map}_{selected_agent}"
        agent = Agent(env, model_path=model_path, learning_rate=learning_rate, gamma=gamma)
        model_file = model_path + "_step_10000.zip"
        if os.path.exists(model_file):
            agent.load(model_file)
            logger.info(f"Loaded pre-trained model from {model_file}")
    else:
        # MODO CORRIDA COMPETITIVA: RaceManager com múltiplos agentes
        print("[MODO] Corrida Competitiva com múltiplos agentes")
        
        # Carrega agentes para competição (o selecionado + rivais do JSON)
        all_agents = [AgentInfo.from_dict(a) for a in load_agents()]
        rivals = [a for a in all_agents if a.nome != agent_info.nome]
        
        # Cria lista de competidores (selecionado + rivais)
        race_agents = [agent_info] + rivals[:n_parallel-1]
        
        # Preenche com clones do agente se faltar
        while len(race_agents) < n_parallel:
            race_agents.append(agent_info)
        
        # Cria ambientes com stats DIFERENTES para cada carro
        # Isso permite visualmente carros com upgrades serem mais rápidos
        env = DummyVecEnv([make_env(selected_map, car_stats=ag.stats) for ag in race_agents])
        
        # Inicializa RaceManager com múltiplos modelos
        race_manager = RaceManager(race_agents, selected_map, n_parallel)
        print(f"[CORRIDA] Competição entre {len(race_agents)} agentes:")
        for i, ag in enumerate(race_agents):
            print(f"  Raia {i}: {ag.nome} (nível {ag.level}, acel {ag.stats['accel']:.2f})")
    
    for i in range(10, 101, 10):
        interface.draw_loading(f'Renderizando agentes... ({i}%)', progresso=i/100, animar=False)
        interface.process_events()
        time.sleep(0.05)

    # 3. Atualiza interface para mostrar que os agentes foram renderizados
    interface.draw_loading('Agentes renderizados! Treinamento iniciado.', progresso=1.0, animar=False)
    interface.update()
    print('Agentes renderizados! Iniciando treinamento...')
    time.sleep(1)

    # 4. Loop principal de treinamento
    training_logger = TrainingLogger()
    # CORREÇÃO: Tratamento de erro para ranking.json
    try:
        interface.load_ranking_data()
    except FileNotFoundError:
        interface.ranking_data = {}
    
    # OTIMIZAÇÃO: Carrega agentes UMA VEZ antes do loop principal
    # Não recarrega a cada episódio (leitura de disco é lenta)
    agents_current = [AgentInfo.from_dict(a) for a in load_agents()]
    agent_info_cache = next((a for a in agents_current if a.nome == interface.selected_agent), None)
    
    logger.info(f"Treinando {n_parallel} execuções paralelas do agente {car_to_train} no mapa: {map_type} (Fase: {fase_desc})")
    obs = env.reset()  # CORREÇÃO: DummyVecEnv.reset() retorna apenas obs
    rewards_hist = [[] for _ in range(n_parallel)]
    collisions_hist = [[] for _ in range(n_parallel)]
    penalties_hist = [[] for _ in range(n_parallel)]
    actions_hist = [[] for _ in range(n_parallel)]
    checkpoints_hist = [[] for _ in range(n_parallel)]
    episodios = [0 for _ in range(n_parallel)]
    ciclo_total = 0
    trajs = [[(obs[i][0], obs[i][1])] for i in range(n_parallel)]
    iter_count = 0
    print("Loop principal iniciado!")
    dones = [False for _ in range(n_parallel)]
    avg_speed = 0.0  # Corrige UnboundLocalError
    n_dif = 0        # Corrige UnboundLocalError
    treino_start = time.time()
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
        # CORREÇÃO: Desenha grid de ambientes simples
        for idx, env_single in enumerate(env.envs):
            interface.draw_env_grid_simple(env_single, idx)
        speeds = []
        unique_states = set()
        
        # ===== LÓGICA HÍBRIDA: TREINO vs CORRIDA =====
        if race_manager:
            # MODO CORRIDA: Múltiplos agentes com seus próprios cérebros
            actions = race_manager.get_actions(obs)
        else:
            # MODO TREINO: Um único agente clonado
            actions_array, _ = agent.model.predict(obs, deterministic=False)
            actions = [int(a) for a in actions_array]  # Converte array para list de ints
        
        # CORREÇÃO: DummyVecEnv.step() sempre retorna 4 valores
        obs_, rewards, dones, infos = env.step(actions)
        terminateds = dones
        truncateds = [False for _ in dones]
        dones = [terminateds[i] or truncateds[i] for i in range(n_parallel)]
        obs = obs_
        for idx in range(n_parallel):
            penalty = min(0, rewards[idx])
            rewards_hist[idx].append(rewards[idx])
            collisions_hist[idx].append(infos[idx]["collisions"] if "collisions" in infos[idx] else 0)
            penalties_hist[idx].append(penalty)
            actions_hist[idx].append(int(actions[idx]))
            checkpoints_hist[idx].append(infos[idx].get("checkpoint", 0))
            speeds.append(abs(obs[idx][2]*2))
            unique_states.add((round(obs[idx][0],1), round(obs[idx][1],1), round(obs[idx][3],1)))
        ciclo_total += sum([1 for d in dones if d])
        avg_speed = sum(speeds)/len(speeds) if speeds else 0.0
        n_dif = len(unique_states)
        interface.draw_dashboard(rewards_hist, collisions_hist, penalties_hist, ciclo_total, avg_speed, n_dif)
        interface.update()
        iter_count += 1
        time.sleep(0.05)
        # Mostra resumo no terminal a cada 20 episódios
        if iter_count % 20 == 0:
            avg_reward = sum([sum(r[-20:]) for r in rewards_hist]) / (20 * n_parallel)
            print(f"[TREINO] Episódio {ciclo_total} | Média recompensa (20): {avg_reward:.2f} | Média velocidade: {avg_speed:.2f}")
        for idx in range(n_parallel):
            if dones[idx]:
                is_success = infos[idx].get('success', False)
                episode_time = infos[idx].get('episode_time', None)
                training_logger.log(idx, rewards_hist[idx], collisions_hist[idx], actions=actions_hist[idx], checkpoints=checkpoints_hist[idx], episode_time=episode_time, success=is_success)
                
                # Atualiza ranking ao final de cada episódio
                key = f"{selected_agent}|{selected_map}"
                score = sum(rewards_hist[idx])
                speed = avg_speed
                tempo = episode_time or 0
                prev = interface.ranking_data.get(key, {"score": -float('inf')})
                if score > prev["score"]:
                    interface.ranking_data[key] = {"score": score, "speed": speed, "tempo": tempo}
                    interface.save_ranking_data()
                
                # OTIMIZAÇÃO: Atualiza o cache em memória em vez de reler do disco
                # Isso reduz I/O e melhora performance
                if agent_info_cache:
                    agent_info_cache.tempo_acumulado += episode_time or 0
                    
                    # Calcula XP baseado no score (gamificação)
                    xp_gained = max(0, int(score * 10))  # 10 XP por ponto de recompensa
                    
                    # Adiciona ao histórico (subjetivação)
                    agent_info_cache.historico.append({
                        "mapa": selected_map,
                        "score": score,
                        "velocidade": speed,
                        "tempo": tempo,
                        "xp_gained": xp_gained,
                        "checkpoints": checkpoints_hist[idx][-1] if checkpoints_hist[idx] else 0,
                        "data": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "tipo_evento": "simulacao"
                    })
                    
                    # Limita histórico para não pesar (últimas 30 corridas)
                    agent_info_cache.historico = agent_info_cache.historico[-30:]
                    
                    # Salva APENAS AQUI (não a cada iteração, apenas ao fim do episódio)
                    agents_all = [AgentInfo.from_dict(a) for a in load_agents()]
                    agents_all = [a.to_dict() if a.nome != agent_info_cache.nome else agent_info_cache.to_dict() for a in agents_all]
                    save_agents(agents_all)
                
                # CORREÇÃO: reset() sempre retorna tuple
                obs_single, _ = env.envs[idx].reset()
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
            # CORREÇÃO: Predição vetorizada
            actions_array, _ = agent.model.predict(states, deterministic=False)
            actions = [int(a) for a in actions_array]  # Converte array para list de ints
            # CORREÇÃO: DummyVecEnv retorna sempre 4 valores
            obs_, rewards, dones, infos = env.step(actions)
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
            # CORREÇÃO: draw_metrics_grid recebe listas de recompensas, não escalares
            interface.dashboard.draw_metrics_grid(rewards_temp, [], [])
            interface.dashboard.draw_info(0)
            interface.update()
            for i in range(n_parallel):
                if dones[i]:
                    episode_rewards[i].append(sum(rewards_temp[i]))
                    episode_checkpoints[i].append(current_checkpoints[i])
                    rewards_temp[i] = []
                    current_checkpoints[i] = 0
                    # CORREÇÃO: Log com scalar, não lista
                    training_logger.log(
                        i,
                        [episode_rewards[i][-1]] if episode_rewards[i] else [0],  # Sempre lista
                        [],  # colisões não são registradas aqui
                        actions=None,
                        checkpoints=[episode_checkpoints[i][-1]] if episode_checkpoints[i] else [0],  # Sempre lista
                        episode_time=None,
                        success=True
                    )
                    # CORREÇÃO: reset() sempre retorna tuple
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
