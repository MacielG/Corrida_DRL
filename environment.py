"""Ambiente de corrida para RL com suporte a escala, tempo, fases e robustez.

Define o ambiente CorridaEnv compatível com OpenAI Gym, incluindo lógica de checkpoints, barreiras, ações e recompensas.
"""
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from config import ENV_SCALE, CAR_LENGTH, CAR_WIDTH, TIME_STEP, RANDOMIZE_START, OBS_NOISE_STD, MAX_STEPS, MAX_EPISODE_TIME, REWARD_SCHEME
import math
from logger import setup_logger
import os
from core.reward_shaper import RewardShapeFactory
from loop_detector import LoopDetector

logger = setup_logger()

class CorridaEnv(gym.Env):
    """Ambiente de corrida customizado para RL.

    Args:
        map_type (str): Tipo de mapa ('corridor' ou 'curve').
        car_stats (dict): Stats do carro {'accel': 0.5, 'turn_speed': 5.0, 'max_speed': 20.0}
    """
    def __init__(self, map_type="corridor", car_stats=None, reward_shaper_type='balanced', reward_config=None):
        self.width = int(800 * ENV_SCALE)
        self.height = int(600 * ENV_SCALE)
        self.map_type = map_type
        self.car1_pos = [150 * ENV_SCALE, 300 * ENV_SCALE]
        self.car1_speed = 0
        self.car1_angle = 0
        self.checkpoints = []
        self.checkpoint_index = 0
        self.barriers = []
        self.corridor_rect = None
        self.max_steps = MAX_STEPS
        self.current_step = 0
        self.episode_time = 0.0
        self.width_norm = 1.0 / self.width
        self.height_norm = 1.0 / self.height
        self.last_angle = None
        self.last_angle_pos = None
        self.n_lidar = 8  # 8 sensores Lidar a cada 45 graus
        self.randomize_checkpoint = False  # Garante que sempre existe
        
        # NOVO: Mecanismos anti-loop
        self.position_history = []  # Track das últimas posições
        self.progress_counter = 0  # Contador de steps sem progresso
        self.max_steps_without_progress = 200  # Falha após ~20s
        self.min_progress_distance = 5 * ENV_SCALE  # Mínimo deslocamento
        self.checkpoints_reached = set()  # Rastreia checkpoints já atingidos neste episódio
        
        # Carrega stats do agente ou usa padrão
        self.car_stats = car_stats if car_stats else {"accel": 0.5, "turn_speed": 5.0, "max_speed": 20.0}
        self.ACCEL_FORCE = self.car_stats["accel"]
        self.TURN_SPEED = self.car_stats["turn_speed"]
        self.MAX_SPEED = self.car_stats["max_speed"]
        
        # Inicializa RewardShaper
        if reward_shaper_type == 'speed':
            config = reward_config or {
                'speed_reward_factor': 2.0,
                'collision_penalty': -100.0,
                'checkpoint_bonus': 50.0
            }
        elif reward_shaper_type == 'safety':
            config = reward_config or {
                'collision_penalty': -200.0,
                'out_of_bounds_penalty': -150.0,
                'smooth_driving_reward': 2.0,
                'checkpoint_bonus': 100.0
            }
        else:  # balanced (default)
            config = reward_config or {
                'checkpoint_reward': 100.0,
                'collision_penalty': -50.0,
                'speed_reward_factor': 0.5,
                'progress_reward_factor': 1.0,
                'out_of_bounds_penalty': -100.0,
                'stability_reward': 1.0
            }
        self.reward_shaper = RewardShapeFactory.create(reward_shaper_type, **config)
        self.last_velocity = 0.0
        
        # Inicializa loop detector
        self.loop_detector = LoopDetector(history_size=100, threshold=0.7)

        # Ações: [acelerar, frear, virar_esquerda, virar_direita]
        self.action_space = spaces.Discrete(4)
        # CORREÇÃO: Estado normalizado - tudo em escala [0,1] ou [-1,1]
        # Estado: [x_norm, y_norm, speed_norm, sin(angle), cos(angle), checkpoint_x_norm, checkpoint_y_norm, lidar...]
        low = np.append(np.array([0, 0, -1, -1, -1, 0, 0]), [0]*self.n_lidar)
        high = np.append(np.array([1, 1, 1, 1, 1, 1, 1]), [1.0]*self.n_lidar)
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)

        self._setup_map()

    def setup_checkpoints(self, map_type, randomize=False):
        """Centraliza a lógica de inicialização de checkpoints.

        Args:
            map_type (str): Tipo de mapa.
            randomize (bool): Se True, randomiza checkpoints.
        Returns:
            list: Lista de tuplas (x, y) dos checkpoints.
        """
        if map_type == "corridor":
            if randomize:
                return [(700 * ENV_SCALE, np.random.uniform(220, 380) * ENV_SCALE)]
            else:
                return [(700 * ENV_SCALE, 300 * ENV_SCALE)]
        elif map_type == "curve":
            if randomize:
                return [
                    (250 * ENV_SCALE, np.random.uniform(120, 300) * ENV_SCALE),
                    (250 * ENV_SCALE, np.random.uniform(100, 200) * ENV_SCALE)
                ]
            else:
                return [
                    (250 * ENV_SCALE, 300 * ENV_SCALE),
                    (250 * ENV_SCALE, 120 * ENV_SCALE)
                ]
        elif map_type == "circle":
            # 4 checkpoints em 0, 90, 180, 270 graus
            center = (400 * ENV_SCALE, 300 * ENV_SCALE)
            radius = 200 * ENV_SCALE
            checkpoints = []
            for i in range(4):
                angle = i * (np.pi/2)
                x = center[0] + radius * np.cos(angle)
                y = center[1] + radius * np.sin(angle)
                checkpoints.append((x, y))
            return checkpoints
        else:
            return []

    def _setup_map(self):
        """Inicializa barreiras, corredor e checkpoints do mapa atual."""
        if self.map_type == "corridor":
            self.corridor_rect = (100 * ENV_SCALE, 200 * ENV_SCALE, 600 * ENV_SCALE, 200 * ENV_SCALE)
            # Barreiras agora ficam fora do retângulo do corredor
            self.barriers = [
                (90 * ENV_SCALE, 200 * ENV_SCALE, 10 * ENV_SCALE, 200 * ENV_SCALE),  # esquerda
                (700 * ENV_SCALE, 200 * ENV_SCALE, 10 * ENV_SCALE, 200 * ENV_SCALE), # direita
            ]
        elif self.map_type == "curve":
            self.corridor_rect = None
            # Barreira esquerda cobre toda a altura desde x=0
            self.barriers = [
                (0, 100 * ENV_SCALE, 100 * ENV_SCALE, 300 * ENV_SCALE),
                (290 * ENV_SCALE, 200 * ENV_SCALE, 10 * ENV_SCALE, 200 * ENV_SCALE),
                (100 * ENV_SCALE, 200 * ENV_SCALE, 200 * ENV_SCALE, 10 * ENV_SCALE),
                (100 * ENV_SCALE, 390 * ENV_SCALE, 200 * ENV_SCALE, 10 * ENV_SCALE),
                (290 * ENV_SCALE, 100 * ENV_SCALE, 10 * ENV_SCALE, 110 * ENV_SCALE),
                (100 * ENV_SCALE, 100 * ENV_SCALE, 10 * ENV_SCALE, 110 * ENV_SCALE),
                (100 * ENV_SCALE, 100 * ENV_SCALE, 200 * ENV_SCALE, 10 * ENV_SCALE),
            ]
        elif self.map_type == "circle":
            self.corridor_rect = None
            self.circle_center = (400 * ENV_SCALE, 300 * ENV_SCALE)
            self.circle_r_in = 150 * ENV_SCALE
            self.circle_r_out = 250 * ENV_SCALE
            self.barriers = []  # Não usa barreiras retangulares
            # Checkpoints em 0, 90, 180, 270 graus
            self.checkpoints = []
            for i in range(4):
                angle = i * (np.pi/2)
                x = self.circle_center[0] + 200 * ENV_SCALE * np.cos(angle)
                y = self.circle_center[1] + 200 * ENV_SCALE * np.sin(angle)
                self.checkpoints.append((x, y))
        else:
            self.corridor_rect = None
            self.barriers = []
        if self.map_type != "circle":
            self.checkpoints = self.setup_checkpoints(self.map_type)

    def reset(self, randomize_checkpoint: bool = False, seed=None, options=None):
        """Reseta o ambiente para o início de um novo episódio.

        Args:
            randomize_checkpoint (bool): Se True, randomiza checkpoints.
        Returns:
            tuple: (obs, info) - Sempre retorna tuple para compatibilidade com Gymnasium.
        """
        self.randomize_checkpoint = randomize_checkpoint
        tentativas = 0
        # Melhora: aumenta a velocidade inicial e garante posição válida
        while True:
            if RANDOMIZE_START:
                self.car1_pos = [
                    150 * ENV_SCALE + np.random.uniform(-20, 20) * ENV_SCALE,
                    300 * ENV_SCALE + np.random.uniform(-20, 20) * ENV_SCALE
                ]
                self.car1_angle = np.random.uniform(-10, 10)  # Começa mais alinhado
            else:
                self.car1_pos = [150 * ENV_SCALE, 300 * ENV_SCALE]
                self.car1_angle = 0
            self.car1_speed = 1.0  # Começa com velocidade positiva
            if self.is_on_corridor(self.car1_pos):
                break
            tentativas += 1
            if (tentativas > 10):
                raise Exception(f"Não foi possível inicializar o carro em posição válida após {tentativas} tentativas!")
        self.checkpoints = self.setup_checkpoints(self.map_type, randomize_checkpoint)
        self.checkpoint_index = 0
        self.current_step = 0
        self.episode_time = 0.0
        self.prev_dist_to_checkpoint = None
        # NOVO: Reset anti-loop
        self.position_history = []
        self.progress_counter = 0
        self.prev_angle = None
        self.checkpoints_reached = set()  # Rastreia checkpoints já atingidos
        # Reset do reward shaper
        self.reward_shaper.reset()
        self.last_velocity = 0.0
        # Reset do loop detector
        self.loop_detector.reset()
        # Sempre retorna observação completa (core + lidar) para compatibilidade com DummyVecEnv
        obs = self._get_obs(only_core=False)
        return np.array(obs, dtype=np.float32), {}

    def get_lidar_readings(self) -> np.ndarray:
        """Simula sensores Lidar em 8 direções (0, 45, ..., 315 graus)."""
        max_dist = 100 * ENV_SCALE
        readings = []
        for i in range(self.n_lidar):
            angle = (self.car1_angle + i*45) % 360
            rad = np.radians(angle)
            for d in np.linspace(5, max_dist, num=20):
                x = self.car1_pos[0] + d * np.cos(rad)
                y = self.car1_pos[1] + d * np.sin(rad)
                if not self.is_on_corridor([x, y]):
                    readings.append(d / max_dist)
                    break
            else:
                readings.append(1.0)
        return np.array(readings, dtype=np.float32)

    def _get_obs(self, only_core=False):
        """Obtém o vetor de observação do estado atual.

        Args:
            only_core (bool): Se True, retorna apenas as 7 primeiras features (sem lidar).
        Returns:
            np.array: Vetor de observação normalizado.
        """
        # Corrige acesso fora do range de checkpoints
        if not self.checkpoints:
            checkpoint = (0, 0)
        elif self.checkpoint_index >= len(self.checkpoints):
            checkpoint = self.checkpoints[-1]
        else:
            checkpoint = self.checkpoints[self.checkpoint_index]
        obs = np.array([
            self.car1_pos[0] * self.width_norm,
            self.car1_pos[1] * self.height_norm,
            self.car1_speed/2.0,
            np.sin(np.radians(self.car1_angle)),
            np.cos(np.radians(self.car1_angle)),
            checkpoint[0] * self.width_norm,
            checkpoint[1] * self.height_norm
        ], dtype=np.float32)
        if only_core:
            return obs
        lidar_readings = self.get_lidar_readings()
        obs = np.concatenate([obs, lidar_readings])
        if OBS_NOISE_STD > 0:
            obs += np.random.normal(0, OBS_NOISE_STD, size=obs.shape)
        return obs

    def step(self, action: int):
         """Executa uma ação no ambiente e retorna o próximo estado."""
         self.current_step += 1
         self.episode_time += TIME_STEP
         
         # Salva estado anterior
         prev_pos = self.car1_pos.copy()
         prev_speed = self.car1_speed
         prev_angle = self.car1_angle
         
         # ===== FÍSICA DO CARRO =====
         FRICTION = 0.98
         if action == 0:
             self.car1_speed = self.car1_speed * FRICTION + self.ACCEL_FORCE
         elif action == 1:
             self.car1_speed = self.car1_speed * FRICTION - self.ACCEL_FORCE
         else:
             self.car1_speed = self.car1_speed * FRICTION
         
         # Limita velocidade máxima
         self.car1_speed = max(-self.MAX_SPEED, min(self.car1_speed, self.MAX_SPEED))
         
         # Rotação
         if action == 2:
             self.car1_angle = (self.car1_angle - self.TURN_SPEED) % 360
         elif action == 3:
             self.car1_angle = (self.car1_angle + self.TURN_SPEED) % 360
         
         # Movimento
         if abs(self.car1_speed) > 0.01:
             rad = np.radians(self.car1_angle)
             delta_x = self.car1_speed * np.cos(rad)
             delta_y = self.car1_speed * np.sin(rad)
             self.car1_pos[0] += delta_x
             self.car1_pos[1] += delta_y
         
         # ===== SISTEMA DE RECOMPENSAS (com RewardShaper) =====
         reward = 0.0
         done = False
         collisions = 0
         success = False
         inside_corridor = self.is_on_corridor(self.car1_pos)
         collision = not inside_corridor
         out_of_bounds = not inside_corridor
         
         # Calcula progresso em direção ao checkpoint
         progress = 0.0
         if self.checkpoints:
             checkpoint = self.checkpoints[self.checkpoint_index]
             dist = np.sqrt((self.car1_pos[0] - checkpoint[0])**2 + (self.car1_pos[1] - checkpoint[1])**2)
             
             # Rastreia progresso anterior
             if self.prev_dist_to_checkpoint is not None:
                 progress = (self.prev_dist_to_checkpoint - dist) / 100.0  # Normaliza
             
             self.prev_dist_to_checkpoint = dist
             
             # Verifica checkpoint atingido
             if dist < 30 * ENV_SCALE and self.checkpoint_index not in self.checkpoints_reached:
                 self.checkpoints_reached.add(self.checkpoint_index)
                 success = True
                 logger.info(f"[CHECKPOINT] Agente atingiu checkpoint {self.checkpoint_index + 1}/{len(self.checkpoints)} em dist={dist:.2f}")
                 self.checkpoint_index += 1
                 
                 if self.checkpoint_index >= len(self.checkpoints):
                     logger.info(f"[SUCESSO] Todos os {len(self.checkpoints)} checkpoints alcançados!")
                     done = True
         
         # Usa RewardShaper para computar recompensa
         reward = self.reward_shaper.compute_reward(
             position=tuple(self.car1_pos),
             velocity=self.car1_speed,
             angle=self.car1_angle,
             checkpoint_idx=self.checkpoint_index,
             total_checkpoints=len(self.checkpoints),
             collision=collision,
             out_of_bounds=out_of_bounds,
             progress=progress,
             last_velocity=self.last_velocity
         )
         
         self.last_velocity = self.car1_speed
         
         # Se saiu do corredor, penaliza fortemente
         if not inside_corridor:
             reward -= 50.0
             done = True
             collisions = 1
         
         # ===== DETECÇÃO DE LOOP/INATIVIDADE (com FFT-based detection) =====
         if self.current_step % 10 == 0:
             self.position_history.append(self.car1_pos.copy())
             self.loop_detector.add_position(tuple(self.car1_pos))
             if len(self.position_history) > 20:
                 self.position_history.pop(0)
         
         # Detecção de loop usando múltiplos métodos
         if self.loop_detector.detect_loop(self.position_history):
             self.progress_counter += 2  # Contagem mais agressiva
             reward -= 5.0  # Penalidade forte por loop detectado
         elif len(self.position_history) >= 2:
             total_distance = 0
             for i in range(1, len(self.position_history)):
                 dist = np.linalg.norm(np.array(self.position_history[i]) - np.array(self.position_history[i-1]))
                 total_distance += dist
             
             if total_distance < self.min_progress_distance:
                 self.progress_counter += 1
                 reward -= 0.2  # Penalidade crescente por inatividade
             else:
                 self.progress_counter = 0
         
         if self.progress_counter > self.max_steps_without_progress:
             reward -= 10.0
             done = True
         
         # ===== LIMITE DE TEMPO =====
         if self.episode_time >= MAX_EPISODE_TIME or self.current_step >= self.max_steps:
             done = True
         
         # ===== RETORNO =====
         obs = np.array(self._get_obs(), dtype=np.float32)
         info = {
             "collisions": collisions,
             "episode_time": self.episode_time,
             "checkpoint": self.checkpoint_index,
             "success": success,
             "progress": self.progress_counter
         }
         return obs, reward, done, False, info

    def is_on_corridor(self, pos):
        """Verifica se uma posição está dentro do corredor e fora das barreiras.

        Args:
            pos (list): Posição [x, y] a ser verificada.
        Returns:
            bool: True se está no corredor, False caso contrário.
        """
        x, y = pos
        if self.map_type == "circle":
            cx, cy = 400 * ENV_SCALE, 300 * ENV_SCALE
            dist = np.sqrt((x - cx)**2 + (y - cy)**2)
            # Limite externo estritamente menor, com tolerância para precisão numérica
            if np.isclose(dist, self.circle_r_out, atol=1e-6):
                inside = False
            else:
                inside = (self.circle_r_in <= dist < self.circle_r_out)
            return inside
        # Primeiro verifica se está dentro de alguma barreira
        for bx, by, bw, bh in self.barriers:
            inside_barrier = (bx <= x <= bx + bw and by <= y <= by + bh)
            if inside_barrier:
                return False
        # Depois verifica se está dentro do corredor
        if self.corridor_rect:
            x0, y0, w, h = self.corridor_rect
            inside_corridor = (x0 <= x <= x0 + w and y0 <= y <= y0 + h)
            if not inside_corridor:
                return False
        return True

    def angle_to_checkpoint(self):
        """Calcula o menor ângulo entre o carro e o próximo checkpoint.

        Returns:
            float: Diferença angular em graus (0 = alinhado).
        """
        pos_tuple = (self.car1_pos[0], self.car1_pos[1], self.car1_angle, self.checkpoints[self.checkpoint_index][0], self.checkpoints[self.checkpoint_index][1])
        if self.last_angle_pos == pos_tuple:
            return self.last_angle
        checkpoint = self.checkpoints[self.checkpoint_index]
        dx = checkpoint[0] - self.car1_pos[0]
        dy = checkpoint[1] - self.car1_pos[1]
        target_angle = (math.degrees(math.atan2(dy, dx)) + 360) % 360
        car_angle = self.car1_angle % 360
        diff = min(abs(target_angle - car_angle), 360 - abs(target_angle - car_angle))
        self.last_angle = diff
        self.last_angle_pos = pos_tuple
        return diff

class MultiAgentEnv:
    """Wrapper para múltiplos ambientes CorridaEnv, gerenciando vários agentes em paralelo.

    Args:
        n_agents (int): Número de agentes/ambientes.
        map_type (str): Tipo de mapa para todos os ambientes.
        car_stats_list (list): Lista de dicts com stats para cada agente.
    """
    def __init__(self, n_agents, map_type, car_stats_list=None):
        if car_stats_list is None:
            car_stats_list = [None] * n_agents
        self.envs = [CorridaEnv(map_type=map_type, car_stats=car_stats_list[i]) for i in range(n_agents)]
        self.n_agents = n_agents
        self.states = [None] * n_agents
        self.dones = [False] * n_agents

    def reset(self):
        """Reseta todos os ambientes e retorna lista de estados."""
        # CORREÇÃO: reset() agora sempre retorna (obs, info) tuple
        self.states = []
        for env in self.envs:
            obs, info = env.reset()  # Sempre tuple
            self.states.append(obs)
        self.dones = [False] * self.n_agents
        return self.states

    def step(self, actions):
        """Executa uma lista de ações, uma para cada agente.

        Args:
            actions (list): Lista de ações (int) para cada agente.
        Returns:
            tuple: (states, rewards, dones, infos) para todos os agentes.
        """
        states, rewards, dones, infos = [], [], [], []
        for i, (env, action) in enumerate(zip(self.envs, actions)):
            if not self.dones[i]:
                # Corrige para aceitar 5 valores do step do CorridaEnv
                state, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                self.states[i] = state
                self.dones[i] = done
            else:
                state, reward, done, info = self.states[i], 0.0, True, {}
            states.append(state)
            rewards.append(reward)
            dones.append(done)
            infos.append(info)
        return states, rewards, dones, infos
