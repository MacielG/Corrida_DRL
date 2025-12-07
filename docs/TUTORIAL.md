# Getting Started - Tutorial Completo

Guia passo-a-passo para começar a usar Corrida DRL.

## 1. Instalação

### Pré-requisitos
- Python 3.10+
- pip

### Setup

```bash
# Clone o repositório
git clone https://github.com/MacielG/Corrida_DRL
cd Corrida_DRL

# Crie um ambiente virtual
python -m venv .venv

# Ative o ambiente
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instale dependências
pip install -r requirements.txt
```

## 2. Estrutura do Projeto

```
Corrida_DRL/
├── environment.py           # Ambiente principal
├── agent.py                # Agente RL
├── main_refactored.py      # Entry point
├── loop_detector.py        # Detector de loops
├── core/
│   ├── reward_shaper.py    # Reward shaping
│   └── ...
├── tests/                  # Testes
├── docs/                   # Documentação
├── models/                 # Modelos treinados
└── logs/                   # Logs de execução
```

## 3. Primeiros Passos

### 3.1 Teste o Ambiente

```python
from environment import CorridaEnv

# Crie um ambiente
env = CorridaEnv(map_type="corridor")

# Resete
obs, info = env.reset()
print(f"Observação shape: {obs.shape}")

# Execute alguns steps
for _ in range(100):
    action = env.action_space.sample()  # Ação aleatória
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"Reward: {reward:.2f}, Done: {terminated}")
    
    if terminated or truncated:
        obs, info = env.reset()
```

### 3.2 Crie um Agente Simples

```python
from agent import Agent
from environment import CorridaEnv

# Ambiente
env = CorridaEnv(map_type="corridor")

# Agente
agent = Agent(env, model_path="models/my_first_agent")

# Treino rápido (1000 timesteps)
print("Treinando...")
agent.train(total_timesteps=1000)

# Avalie
obs, _ = env.reset()
for _ in range(100):
    action, _ = agent.predict(obs, deterministic=True)
    obs, reward, done, _, _ = env.step(action)
    if done:
        break

print("✅ Agente treinado!")
```

## 4. Reward Shaping

### 4.1 Entender Reward Shapers

Existem 3 tipos principais:

**Balanced (Padrão)**
- Equilibra checkpoint + velocidade + penalidades
- Bom para treino geral

```python
env = CorridaEnv(reward_shaper_type='balanced')
```

**Speed**
- Foca em velocidade máxima (racing puro)
- Penaliza colisões fortemente

```python
env = CorridaEnv(reward_shaper_type='speed')
```

**Safety**
- Foca em direção suave e estável
- Penaliza colisões e saídas da pista

```python
env = CorridaEnv(reward_shaper_type='safety')
```

### 4.2 Customizar Recompensas

```python
from environment import CorridaEnv

custom_config = {
    'checkpoint_reward': 200.0,   # Aumenta bônus por checkpoint
    'collision_penalty': -100.0,  # Penaliza mais colisões
    'speed_reward_factor': 2.0,   # Valoriza velocidade
}

env = CorridaEnv(
    reward_shaper_type='balanced',
    reward_config=custom_config
)
```

## 5. Treino Passo-a-Passo

### 5.1 Treino Simples

```python
from agent import Agent
from environment import CorridaEnv
import numpy as np

# Setup
env = CorridaEnv(map_type="corridor")
agent = Agent(env, model_path="models/simple_train")

# Treino
print("Iniciando treino...")
agent.train(total_timesteps=50000)
agent.save("models/simple_train.zip")

# Teste
print("Testando...")
obs, _ = env.reset()
episode_reward = 0
for _ in range(500):
    action, _ = agent.predict(obs, deterministic=True)
    obs, reward, done, _, _ = env.step(action)
    episode_reward += reward
    if done:
        obs, _ = env.reset()

print(f"✅ Treino completo! Recompensa: {episode_reward:.2f}")
```

### 5.2 Treino com Múltiplos Ambientes (Paralelo)

```python
from stable_baselines3.common.vec_env import DummyVecEnv
from agent import Agent
from environment import CorridaEnv

# Crie múltiplos ambientes
def make_env(rank):
    def _init():
        env = CorridaEnv(map_type="corridor")
        return env
    return _init

# 4 ambientes em paralelo
num_envs = 4
env = DummyVecEnv([make_env(i) for i in range(num_envs)])

# Agente
agent = Agent(env, model_path="models/parallel_train")

# Treino (4x mais rápido!)
print("Treino em 4 ambientes paralelos...")
agent.train(total_timesteps=100000)
agent.save("models/parallel_train.zip")

print("✅ Treino paralelo completo!")
```

## 6. Loop Detection

O ambiente detecta automaticamente loops usando FFT.

```python
from environment import CorridaEnv

env = CorridaEnv()
env.reset()

for i in range(500):
    action = 3  # Sempre vira direita (cria loop)
    obs, reward, done, _, _ = env.step(action)
    
    # Loop detector ativo
    loop_score = env.loop_detector.get_loop_score()
    print(f"Step {i}: Loop score: {loop_score:.2f}")
    
    if done:
        print("✅ Loop detectado e penalizado!")
        break
```

## 7. Uso da Interface Gráfica

```bash
# Execute o main refatorado
python main_refactored.py
```

Funcionalidades:
- Menu de seleção de agentes
- Escolha de mapa
- Visualização em tempo real
- Dashboard com métricas
- Ranking de agentes

## 8. Avaliação e Métricas

### 8.1 Avaliar Agente

```python
from agent import Agent
from environment import CorridaEnv
import numpy as np

env = CorridaEnv()
agent = Agent(env)
agent.load("models/my_agent.zip")

# Avalie em 10 episódios
episodes = 10
rewards = []

for ep in range(episodes):
    obs, _ = env.reset()
    episode_reward = 0
    done = False
    
    while not done:
        action, _ = agent.predict(obs, deterministic=True)
        obs, reward, done, _, _ = env.step(action)
        episode_reward += reward
    
    rewards.append(episode_reward)

print(f"Média: {np.mean(rewards):.2f} ± {np.std(rewards):.2f}")
```

### 8.2 Visualizar Treino

```python
# Os logs estão em logs/
# Visualize com:
import json

with open("logs/session_YYYYMMDD_HHMMSS/treinados_sucesso_*.txt") as f:
    print(f.read())
```

## 9. Testes

```bash
# Execute todos os testes
python -m pytest tests/ -v

# Teste específico
python -m pytest tests/test_reward_shaper_integration.py -v

# Com cobertura
python -m pytest tests/ --cov=. --cov-report=html
```

## 10. Salvar e Carregar Modelos

```python
from agent import Agent
from environment import CorridaEnv

# Treino
env = CorridaEnv()
agent = Agent(env, model_path="models/my_model")
agent.train(total_timesteps=100000)

# Salvar
agent.save("models/my_model_final.zip")
print("✅ Modelo salvo!")

# Carregar
agent2 = Agent(env, model_path="models/my_model")
agent2.load("models/my_model_final.zip")
print("✅ Modelo carregado!")

# Usar
obs, _ = env.reset()
action, _ = agent2.predict(obs)
```

## 11. Troubleshooting

### Erro: "CUDA out of memory"
Reduza `n_parallel` em `config.py`

### Erro: "No module named 'environment'"
Certifique-se de estar no diretório correto:
```bash
cd Corrida_DRL
python script.py
```

### Treino muito lento
```python
# Use speed shaper (menos cálculos)
env = CorridaEnv(reward_shaper_type='speed')

# Aumente batch size
agent.train(total_timesteps=100000)  # Maior timesteps
```

### Reward NaN
```python
# Verifique observação
obs, _ = env.reset()
print(f"Obs válida: {np.isfinite(obs).all()}")

# Se tiver NaN, ambiente tem problema
```

## 12. Próximos Passos

1. **Customize reward shaping** para seu caso de uso
2. **Teste diferentes mapas** (corridor, curve, circle)
3. **Compare diferentes shapers** (balanced, speed, safety)
4. **Aumente dataset** de treino (mais timesteps)
5. **Deploy modelo** em produção
6. **Contribua melhorias** ao repositório!

## 13. Recursos Adicionais

- [API Reference](API.md) - Documentação completa
- [Loop Detection](../loop_detector.py) - Código fonte
- [Reward Shaper](../core/reward_shaper.py) - Código fonte
- [Tests](../tests/) - Exemplos de uso

---

**Boa sorte! 🏎️**

Se tiver dúvidas, abra uma issue no GitHub ou consulte a documentação completa em `docs/`.
