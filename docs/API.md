# API Reference - Corrida DRL

Documentação completa da API do projeto de Deep Reinforcement Learning para corrida.

## Table of Contents
- [Módulos Principais](#módulos-principais)
- [Environment](#environment)
- [Agent](#agent)
- [Reward Shaping](#reward-shaping)
- [Loop Detection](#loop-detection)
- [Main](#main)

---

## Módulos Principais

### `environment.py`
Ambiente OpenAI Gym para simulação de corridas com RL.

### `agent.py`
Implementação do agente de RL usando Stable Baselines3.

### `core/reward_shaper.py`
Sistema modular de recompensas configurável.

### `loop_detector.py`
Detector de loops usando FFT e análise de trajetória.

### `main_refactored.py`
Entry point refatorado com separação clara de concerns.

---

## Environment

### `CorridaEnv`

Ambiente principal para treino de agentes. Compatível com OpenAI Gym/Gymnasium.

#### Inicialização

```python
from environment import CorridaEnv

# Padrão (balanced reward shaper)
env = CorridaEnv(map_type="corridor")

# Com speed shaper (racing puro)
env = CorridaEnv(map_type="corridor", reward_shaper_type='speed')

# Com safety shaper (estabilidade)
env = CorridaEnv(map_type="corridor", reward_shaper_type='safety')

# Custom reward config
env = CorridaEnv(
    map_type="corridor",
    reward_shaper_type='balanced',
    reward_config={
        'checkpoint_reward': 200.0,
        'collision_penalty': -100.0,
        'speed_reward_factor': 2.0
    }
)
```

#### Métodos Principais

##### `reset(randomize_checkpoint=False, seed=None, options=None)`
Reseta o ambiente para novo episódio.

**Returns:**
- `obs` (np.ndarray): Observação inicial
- `info` (dict): Informações adicionais

```python
obs, info = env.reset()
```

##### `step(action)`
Executa uma ação e retorna o próximo estado.

**Args:**
- `action` (int): Uma de 4 ações [accelerate, brake, turn_left, turn_right]

**Returns:**
- `obs` (np.ndarray): Nova observação
- `reward` (float): Recompensa do step
- `terminated` (bool): Se episódio terminou
- `truncated` (bool): Se episódio foi truncado
- `info` (dict): Informações adicionais

```python
obs, reward, terminated, truncated, info = env.step(action)
```

#### Action Space
- `0`: Acelerar
- `1`: Frear
- `2`: Virar esquerda
- `3`: Virar direita

#### Observation Space
Estado normalizado com 15 dimensões:
1. `x_norm`: Posição X normalizada [0, 1]
2. `y_norm`: Posição Y normalizada [0, 1]
3. `speed_norm`: Velocidade normalizada [-1, 1]
4. `sin(angle)`: Seno do ângulo [-1, 1]
5. `cos(angle)`: Coseno do ângulo [-1, 1]
6. `checkpoint_x_norm`: Coordenada X do checkpoint [0, 1]
7. `checkpoint_y_norm`: Coordenada Y do checkpoint [0, 1]
8-15. Leitura de 8 sensores Lidar [0, 1]

#### Propriedades Importantes
- `map_type` (str): 'corridor', 'curve', ou 'circle'
- `car_stats` (dict): {'accel', 'turn_speed', 'max_speed'}
- `reward_shaper`: Instância do RewardShaper ativo
- `loop_detector`: Detector de loops FFT-based
- `checkpoint_index`: Checkpoint atual
- `episode_time`: Tempo desde início do episódio

#### Info Dictionary
Retornado no `step()`:
```python
{
    'collisions': int,           # Número de colisões
    'episode_time': float,       # Tempo de episódio
    'checkpoint': int,           # Checkpoint atual
    'success': bool,             # Se sucesso
    'progress': int              # Contador de progresso
}
```

---

## Agent

### `Agent`

Agente baseado em Stable Baselines3 (PPO).

#### Inicialização

```python
from agent import Agent
from environment import CorridaEnv

env = CorridaEnv()
agent = Agent(env, model_path="models/my_agent")
```

#### Métodos Principais

##### `train(total_timesteps)`
Treina o agente.

```python
agent.train(total_timesteps=10000)
```

##### `predict(obs, deterministic=False)`
Prediz ação para observação.

```python
action, _ = agent.predict(obs, deterministic=True)
```

##### `save(path)`
Salva modelo treinado.

```python
agent.save("models/my_model.zip")
```

##### `load(path)`
Carrega modelo salvo.

```python
agent.load("models/my_model.zip")
```

---

## Reward Shaping

### `RewardShapeFactory`

Factory para criar diferentes tipos de reward shapers.

```python
from core.reward_shaper import RewardShapeFactory

# Tipos disponíveis: 'balanced', 'speed', 'safety'
shaper = RewardShapeFactory.create('balanced')
```

### `BalancedRewardShaper`

Recompensa equilibrada entre checkpoints, velocidade e penalidades.

**Parâmetros:**
- `checkpoint_reward` (float): Recompensa por checkpoint (default: 100.0)
- `collision_penalty` (float): Penalidade por colisão (default: -50.0)
- `speed_reward_factor` (float): Fator de recompensa por velocidade (default: 0.5)
- `progress_reward_factor` (float): Fator de recompensa por progresso (default: 1.0)
- `out_of_bounds_penalty` (float): Penalidade por sair da pista (default: -100.0)
- `stability_reward` (float): Recompensa por estabilidade (default: 1.0)

### `SpeedRewardShaper`

Recompensa focada em velocidade pura (racing).

**Parâmetros:**
- `speed_reward_factor` (float): Fator de velocidade (default: 2.0)
- `collision_penalty` (float): Penalidade por colisão (default: -100.0)
- `checkpoint_bonus` (float): Bônus por checkpoint (default: 50.0)

### `SafetyRewardShaper`

Recompensa focada em estabilidade e segurança.

**Parâmetros:**
- `collision_penalty` (float): Penalidade por colisão (default: -200.0)
- `out_of_bounds_penalty` (float): Penalidade por sair da pista (default: -150.0)
- `smooth_driving_reward` (float): Recompensa por direção suave (default: 2.0)
- `checkpoint_bonus` (float): Bônus por checkpoint (default: 100.0)

#### Método `compute_reward()`

```python
reward = shaper.compute_reward(
    position=(x, y),
    velocity=speed,
    angle=angle_deg,
    checkpoint_idx=current_checkpoint,
    total_checkpoints=total_checkpoints,
    collision=collision_bool,
    out_of_bounds=out_of_bounds_bool,
    progress=progress_value,
    last_velocity=last_velocity
)
```

---

## Loop Detection

### `LoopDetector`

Detector de loops usando FFT e análise de trajetória.

#### Inicialização

```python
from loop_detector import LoopDetector

detector = LoopDetector(history_size=100, threshold=0.7)
```

#### Métodos Principais

##### `add_position(position)`
Adiciona posição ao histórico.

```python
detector.add_position((x, y))
```

##### `detect_loop(position_history=None)`
Detecta loop usando múltiplos métodos.

**Returns:** bool (True se loop detectado)

```python
is_loop = detector.detect_loop()
```

##### `detect_loop_fft()`
Detecta loop usando FFT.

```python
is_loop = detector.detect_loop_fft()
```

##### `detect_loop_correlation()`
Detecta loop usando auto-correlação.

```python
is_loop = detector.detect_loop_correlation()
```

##### `detect_loop_distance()`
Detecta loop verificando distância circular.

```python
is_loop = detector.detect_loop_distance()
```

##### `get_loop_score()`
Retorna score de loop (0-1).

```python
score = detector.get_loop_score()  # 0=sem loop, 1=loop forte
```

##### `reset()`
Reseta o detector.

```python
detector.reset()
```

---

## Main

### `main()`

Função principal que coordena interface, setup de agentes e loop de treinamento.

```python
from main_refactored import main

main(
    map_type="corridor",
    car_to_train=1,
    fase_idx=0,
    n_parallel=8,
    skip_training=False,
    learning_rate=0.0003,
    gamma=0.99
)
```

**Parâmetros:**
- `map_type` (str): Tipo de mapa ('corridor', 'curve', 'circle')
- `car_to_train` (int): Índice do carro a treinar
- `fase_idx` (int): Índice da fase de treinamento
- `n_parallel` (int): Número de ambientes paralelos
- `skip_training` (bool): Se True, carrega modelo pré-treinado e executa corrida competitiva
- `learning_rate` (float): Taxa de aprendizado
- `gamma` (float): Fator de desconto

### `RaceManager`

Gerenciador de corridas competitivas multi-agentes.

```python
from main_refactored import RaceManager

race_manager = RaceManager(
    agents_info_list=agents,
    map_type="corridor",
    n_parallel=4
)
```

#### Métodos

##### `get_actions(observations)`
Prediz ações para múltiplos agentes.

```python
actions = race_manager.get_actions(observations)
```

##### `update_score(agent_name, reward)`
Atualiza score de um agente.

```python
race_manager.update_score("agent_1", 50.0)
```

##### `get_final_ranking()`
Retorna ranking final.

```python
ranking = race_manager.get_final_ranking()  # [(name, score), ...]
```

##### `save_race_history(filename)`
Salva histórico em JSON.

```python
race_manager.save_race_history("race_results.json")
```

##### `load_race_history(filename)`
Carrega histórico de JSON.

```python
race_manager.load_race_history("race_results.json")
```

---

## Exemplo Completo

```python
from environment import CorridaEnv
from agent import Agent
import numpy as np

# Criar ambiente
env = CorridaEnv(
    map_type="corridor",
    reward_shaper_type='balanced'
)

# Criar agente
agent = Agent(env, model_path="models/my_agent")

# Treino
agent.train(total_timesteps=100000)

# Avaliação
obs, _ = env.reset()
done = False
episode_reward = 0

while not done:
    action, _ = agent.predict(obs, deterministic=True)
    obs, reward, terminated, truncated, info = env.step(action)
    episode_reward += reward
    done = terminated or truncated

print(f"Recompensa total: {episode_reward:.2f}")

# Salvar
agent.save("models/my_agent_trained.zip")
```

---

## Configuração

Veja `config.py` para parâmetros globais:
- `ENV_SCALE`: Escala do ambiente
- `MAX_STEPS`: Máximo de steps por episódio
- `MAX_EPISODE_TIME`: Tempo máximo por episódio
- `REWARD_SCHEME`: Esquema de recompensas

---

## Troubleshooting

### Import Errors
Certifique-se de estar no diretório do projeto:
```bash
cd Corrida_DRL
python -c "from environment import CorridaEnv; print('OK')"
```

### Reward NaN
Se receber recompensas NaN, verifique:
1. Posição está válida
2. Loop detector não está criando loops infinitos
3. Reward shaper foi inicializado

### Slow Training
Para acelerar:
1. Aumente `n_parallel` em `config.py`
2. Use `reward_shaper_type='speed'` para menos cálculos
3. Reduza observação para apenas core (sem lidar)

---

**Última atualização:** 2025-12-07  
**Versão:** 2.0
