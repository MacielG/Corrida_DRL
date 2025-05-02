"""Configurações globais do ambiente Corrida DRL.

Contém constantes de escala, parâmetros do carro, limites de tempo, ruído de observação, etc.
"""

"""
Arquivo de configuração central do projeto Corrida DRL.
Altere os parâmetros abaixo para controlar escala, tempo, fases e robustez.
"""

import json
import os

# Escala do ambiente (1.0 = padrão, 2.0 = dobro do tamanho, etc.)
ENV_SCALE = 1.0

# Tamanho do carro em pixels (ajustado pela escala)
CAR_LENGTH = 40 * ENV_SCALE
CAR_WIDTH = 20 * ENV_SCALE

# Passo de tempo em segundos
TIME_STEP = 0.1  # Pode ser ajustado para 0.2 se quiser mais avanço

# Velocidade da simulação (1.0 = tempo real, 2.0 = 2x mais rápido)
SIM_SPEED = 1.0

# Fases disponíveis para curriculum learning
PHASES = [
    {"map_type": "corridor", "desc": "Corredor reto"},
    {"map_type": "curve", "desc": "Corredor com curva"},
    {"map_type": "circle", "desc": "Pista circular"},
]

# Robustez
RANDOMIZE_START = True  # Randomizar posição/velocidade inicial
OBS_NOISE_STD = 0.01    # Desvio padrão do ruído nas observações

# Limite de passos por episódio
MAX_STEPS = 1000  # Aumentado para dar mais tempo de exploração

# Limite de tempo de episódio em segundos
MAX_EPISODE_TIME = 15.0  # Reduzido para limitar cada ciclo a 15 segundos

# Esquema de recompensa
REWARD_SCHEME = "dense"  # Opções: "sparse", "dense"

# Algoritmo de RL
RL_ALGORITHM = "DQN"
SUPPORTED_ALGORITHMS = ["DQN", "PPO", "SAC"]

"""
Plano de currículo estruturado para o agente RL:
- O agente começa em mapas simples e só avança para mapas mais difíceis ao atingir desempenho mínimo.
- O desempenho é avaliado por média de recompensas e/ou número de checkpoints atingidos em N episódios.
- O currículo é definido em etapas, cada uma com mapa, critérios de avanço e parâmetros opcionais.
"""

CURRICULUM = [
    {
        "map_type": "corridor",
        "desc": "Corredor reto",
        "min_reward": 50,          # Valor mais fácil para começar
        "min_checkpoints": 1,      # Exigência inicial menor
        "episodes_eval": 10,       # Janela menor para facilitar avanço
        "max_steps": 1000          # Mais tempo para explorar
    },
    {
        "map_type": "curve",
        "desc": "Corredor com curva",
        "min_reward": 100,
        "min_checkpoints": 2,
        "episodes_eval": 10,
        "max_steps": 1000
    },
    {
        "map_type": "circle",
        "desc": "Pista circular",
        "min_reward": 150,
        "min_checkpoints": 4,
        "episodes_eval": 10,
        "max_steps": 2000
    },
    # Adicione mais etapas conforme desejar
]

def load_config(file="config.json"):
    """Carrega hiperparâmetros de um arquivo JSON e mescla com valores padrão."""
    defaults = {
        "learning_rate": 0.0003,
        "gamma": 0.98,
        "n_parallel": 4,
        "map_type": "corridor"
    }
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            defaults.update(user_cfg)
        except json.JSONDecodeError:
            pass  # Return defaults on invalid JSON
    return defaults
