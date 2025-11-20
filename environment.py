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

logger = setup_logger()

class CorridaEnv(gym.Env):
    """Ambiente de corrida customizado para RL.

    Args:
        map_type (str): Tipo de mapa ('corridor' ou 'curve').
        car_stats (dict): Stats do carro {'accel': 0.5, 'turn_speed': 5.0, 'max_speed': 20.0}
    """
    def __init__(self, map_type="corridor", car_stats=None):
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
        
        # Carrega stats do agente ou usa padrão
        self.car_stats = car_stats if car_stats else {"accel": 0.5, "turn_speed": 5.0, "max_speed": 20.0}
        self.ACCEL_FORCE = self.car_stats["accel"]
        self.TURN_SPEED = self.car_stats["turn_speed"]
        self.MAX_SPEED = self.car_stats["max_speed"]

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
        self.prev_angle = None
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
        """Executa uma ação no ambiente e retorna o próximo estado.
        
        Args:
            action (int): Ação a ser executada (0: acelerar, 1: frear, 2: virar esquerda, 3: virar direita).
        Returns:
            tuple: (state, reward, done, info) onde:
                - state (np.array): Novo estado do ambiente.
                - reward (float): Recompensa pela ação.
                - done (bool): Indica se o episódio terminou.
                - info (dict): Informações adicionais (colisões, checkpoint, etc.).
        """
        self.current_step += 1
        self.episode_time += TIME_STEP
        reward = 0  # Inicializa reward antes de qualquer uso
        prev_pos = self.car1_pos.copy()
        prev_speed = self.car1_speed
        prev_angle = self.car1_angle
        prev_pos_before_move = self.car1_pos.copy()
        # Ação do carro 1 (agente)
        # Física realista: força e atrito com stats dinâmicos
        FRICTION = 0.98
        if action == 0:
            self.car1_speed = self.car1_speed * FRICTION + self.ACCEL_FORCE
        elif action == 1:
            self.car1_speed = self.car1_speed * FRICTION - self.ACCEL_FORCE
        else:
            self.car1_speed = self.car1_speed * FRICTION
        
        # Limita velocidade máxima baseada em stats
        self.car1_speed = max(-self.MAX_SPEED, min(self.car1_speed, self.MAX_SPEED))
        
        if action == 2:
            self.car1_angle = (self.car1_angle - self.TURN_SPEED) % 360
        elif action == 3:
            self.car1_angle = (self.car1_angle + self.TURN_SPEED) % 360
        if abs(self.car1_speed) > 0.01:
            rad = np.radians(self.car1_angle)
            delta_x = self.car1_speed * np.cos(rad)
            delta_y = self.car1_speed * np.sin(rad)
            # Calcula vetor de movimento real
            move_vec = np.array([delta_x, delta_y])
            # Calcula vetor direção do carro
            angle_vec = np.array([np.cos(rad), np.sin(rad)])
            # Penaliza drift lateral (movimento desalinhado)
            if np.linalg.norm(move_vec) > 0:
                move_dir = move_vec / (np.linalg.norm(move_vec) + 1e-8)
                alignment = np.dot(move_dir, angle_vec)
                if alignment < 0.98:  # 1.0 = alinhado, <0.98 = drift
                    reward -= (1 - alignment) * 0.5  # penalidade suave
            self.car1_pos[0] += delta_x
            self.car1_pos[1] += delta_y
        inside_corridor = self.is_on_corridor(self.car1_pos)

        reward = 0
        done = False
        collisions = 0
        penalty = 0
        success = False

        if not inside_corridor:
            reward = -3
            done = True
            collisions = 1
            # Retorna imediatamente para não somar penalidades extras
            state = self._get_obs()
            info = {"collisions": collisions, "episode_time": self.episode_time, "checkpoint": self.checkpoint_index, "penalty": penalty, "success": success}
            obs = np.array(self._get_obs(), dtype=np.float32)
            terminated = done
            truncated = False
            return obs, reward, terminated, truncated, info
        else:
            reward = -0.001
            if self.car1_speed < 0:
                reward -= 0.1  # Penalidade maior para andar para trás
            dist_moved = np.linalg.norm(np.array(self.car1_pos) - np.array(prev_pos))
            if dist_moved > 0.05 and self.checkpoints:
                reward += 0.2  # Bônus maior por movimento
            if self.checkpoints:
                checkpoint = self.checkpoints[self.checkpoint_index]
                dist = np.sqrt((self.car1_pos[0] - checkpoint[0])**2 + (self.car1_pos[1] - checkpoint[1])**2)
                if self.prev_dist_to_checkpoint is not None:
                    progress = self.prev_dist_to_checkpoint - dist
                    reward += max(0, progress) * 4.0  # Peso maior para progresso
                self.prev_dist_to_checkpoint = dist
                angle_diff = self.angle_to_checkpoint()
                reward += np.cos(np.radians(angle_diff)) * 0.2  # Bônus angular maior
                if abs(prev_speed) < 0.05:
                    reward = -0.5
                # NOVO: Aumenta densidade de recompensa por velocidade
                reward += (self.car1_speed / 20.0) * 0.1  # Incentiva movimento constante
                # NOVO: Penalidade por tempo (incentiva terminar rápido)
                reward -= 0.005
            else:
                reward += 0.0

        # Recompensa densa/esparsa
        if REWARD_SCHEME == "dense" and self.checkpoints:
            # Centralização
            if self.map_type == "corridor":
                center_y = 300 * ENV_SCALE
                reward += -0.03 * abs(self.car1_pos[1] - center_y) / ENV_SCALE
            elif self.map_type == "curve":
                checkpoint = self.checkpoints[self.checkpoint_index] if self.checkpoints else (0, 0)
                dist_to_cp = np.linalg.norm(np.array(self.car1_pos) - np.array(checkpoint))
                reward += -0.008 * dist_to_cp / ENV_SCALE
            # Suavidade de ação
            if hasattr(self, 'last_action') and self.last_action is not None and action != self.last_action:
                reward -= 0.03
            self.last_action = action
        elif REWARD_SCHEME == "sparse":
            self.last_action = action
            # Remove componentes densos
            pass
        else:
            self.last_action = action

        # Usa checkpoint padrão se a lista estiver vazia
        checkpoint = self.checkpoints[self.checkpoint_index] if self.checkpoints else (0, 0)
        dx = checkpoint[0] - self.car1_pos[0]
        dy = checkpoint[1] - self.car1_pos[1]
        target_angle = (math.degrees(math.atan2(dy, dx)) + 360) % 360
        car_angle = self.car1_angle % 360
        diff_angle = min(abs(target_angle - car_angle), 360 - abs(target_angle - car_angle))
        if diff_angle < 10:
            reward += 0.3  # Bônus maior por alinhamento

        dist = np.sqrt((self.car1_pos[0] - checkpoint[0])**2 + (self.car1_pos[1] - checkpoint[1])**2)
        angle_diff = self.angle_to_checkpoint() if self.checkpoints else 0
        # Removido print DEBUG para não travar interface
        # print(f"[DEBUG] dist={dist}, angle_diff={angle_diff}, car1_pos={self.car1_pos}, checkpoint={checkpoint}")
        # Alteração: sucesso se dist < 20*ENV_SCALE e ângulo < 30 OU dist ~ 0
        if self.checkpoints and ((dist < 20 * ENV_SCALE and angle_diff < 30) or np.isclose(dist, 0, atol=1e-6)):
            reward += 20.0  # Recompensa irresistível por checkpoint (aumentado de 12)
            self.checkpoint_index += 1
            success = True
            if self.checkpoint_index >= len(self.checkpoints):
                reward += 50.0  # Bônus adicional por completar todos os checkpoints
                done = True

        if self.randomize_checkpoint and success:
            self.checkpoints = self.setup_checkpoints(self.map_type, self.randomize_checkpoint)
        elif not self.checkpoints:
            self.checkpoints = self.setup_checkpoints(self.map_type)

        if self.episode_time >= MAX_EPISODE_TIME:
            done = True
        if self.current_step >= self.max_steps:
            done = True

        state = self._get_obs()
        info = {"collisions": collisions, "episode_time": self.episode_time, "checkpoint": self.checkpoint_index, "penalty": penalty, "success": success}
        # Garante compatibilidade com Gymnasium: retorna obs, reward, terminated, truncated, info
        obs = np.array(self._get_obs(), dtype=np.float32)
        terminated = done
        truncated = False
        return obs, reward, terminated, truncated, info

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
