# Sistema de Gamificação - Corrida DRL v2.1

## Visão Geral

A **Camada de Gamificação** transforma o projeto de um "experimento acadêmico de RL" para um **"Jogo Completo de Gerenciamento de Equipe de Corrida com IA"**, com as 3 peças-chave implementadas:

1. **🏎️ Corridas Coletivas** - Múltiplos agentes com diferentes modelos competem simultaneamente
2. **🔧 Upgrades e Física Variável** - O jogador evolui o carro com stats customizados
3. **🗺️ Progressão e Desbloqueios** - Mapas e upgrades desbloqueados por nível

---

## 1. Upgrades e Física Variável

### Como Funciona

Cada agente possui **3 stats que afetam a física do carro**:

- **Aceleração** (padrão: 0.5, máximo: 1.0)
  - Aumenta a taxa de aceleração do carro
  - Custo: 100 XP por upgrade
  - Incremento: +0.05 por upgrade

- **Velocidade de Virada** (padrão: 5.0 graus, máximo: 15.0)
  - Melhora a resposta de direção
  - Custo: 80 XP por upgrade
  - Incremento: +0.5 graus por upgrade

- **Velocidade Máxima** (padrão: 20.0 unidades, máximo: 30.0)
  - Limita a velocidade do carro
  - Custo: 150 XP por upgrade
  - Incremento: +1.0 unidades por upgrade

### Implementação no Código

**Environment (`environment.py`)**:
```python
# CorridaEnv aceita stats customizados
env = CorridaEnv(map_type="corridor", car_stats={
    "accel": 0.6,        # Acelerado
    "turn_speed": 7.0,
    "max_speed": 22.0
})

# Na física do step():
if action == 0:
    self.car1_speed = self.car1_speed * FRICTION + self.ACCEL_FORCE
self.car1_speed = max(-self.MAX_SPEED, min(self.car1_speed, self.MAX_SPEED))
```

**Agentes (`interface_agents.py`)**:
```python
agent = AgentInfo("MeuBot", "PPO", stats={
    "accel": 0.5,
    "turn_speed": 5.0,
    "max_speed": 20.0
}, level=1)

# Aplicar upgrade
agent.upgrade("accel")  # Incrementa aceleração e sobe nível
```

### Efeito Visual

No `main.py`, os stats são exibidos ao iniciar a simulação:
```
[GAMIFICAÇÃO] Stats do agente: Acel=0.6, Turn=7.0, MaxSpeed=22.0
[GAMIFICAÇÃO] Nível do agente: 3
```

E aparecem no **Ranking** junto com o score do agente.

---

## 2. Corridas Coletivas (Multi-Modelos)

### Como Funciona

A classe `RaceManager` permite que **múltiplos agentes treinados compitam simultaneamente**, cada um usando seu próprio modelo neural.

**Cenário**: 
- Agente "PowerBot" (treinado com PPO) contra
- Agente "SpeedBot" (treinado com DQN) contra
- Agente "BalanceBot" (treinado com SAC)
- Todos no mesmo mapa, simultaneamente

### Arquitetura

```
RaceManager
├── models: [Agent(PPO), Agent(DQN), Agent(SAC)]
├── agent_stats: [{accel: 0.5, ...}, {accel: 0.6, ...}, ...]
└── get_actions(observations) → [action_0, action_1, action_2, ...]
    └── Cada agente usa seu próprio modelo para predição
```

### Implementação no Código

**`main.py` - Classe RaceManager**:
```python
class RaceManager:
    def __init__(self, agents_info_list, map_type, n_parallel=8):
        # Carrega múltiplos modelos
        for agent_info in agents_info_list:
            model = Agent(env, model_path=agent_info.modelo_path)
            model.load(agent_info.modelo_path)
            self.models.append(model)
    
    def get_actions(self, observations):
        # Cada índice i usa modelo i % len(models)
        for i, obs in enumerate(observations):
            model_idx = i % len(self.models)
            action, _ = self.models[model_idx].predict(obs)
            actions.append(int(action))
        return actions
```

**Uso no Loop Principal**:
```python
race_manager = RaceManager(
    agents_info_list=[top_4_agents],
    map_type="corridor",
    n_parallel=8
)

# No loop
actions = race_manager.get_actions(obs)  # Predições de múltiplos modelos
obs_, rewards, dones, infos = env.step(actions)
```

### Arquivo Separado: `race_manager.py`

Contém classes avançadas para gerenciamento de corridas:

- **`RaceResult`**: Armazena resultados de uma corrida
- **`CompetitiveRaceManager`**: Gerencia torneios round-robin

```python
from race_manager import CompetitiveRaceManager

race_mgr = CompetitiveRaceManager(map_type="circle", top_n=4)
race_mgr.load_top_agents()
result = race_mgr.run_race(max_steps=500)

print(f"Vencedor: {result.get_winner()}")
```

---

## 3. Progressão e Desbloqueios

### Sistema de Níveis

A fórmula de nível baseada em XP é **exponencial**:

```
Nível = floor(sqrt(XP / 100)) + 1

XP necessário por nível:
- Nível 1: 0 XP (início)
- Nível 2: 100 XP
- Nível 3: 400 XP
- Nível 4: 900 XP
- Nível 5: 1600 XP
- Nível 10: 8100 XP
```

### Desbloqueio de Mapas

| Mapa | Nível Requerido | Dificuldade |
|------|-----------------|-------------|
| `corridor` | 1 (inicial) | Fácil |
| `curve` | 5 | Médio |
| `circle` | 10 | Difícil |

**Implementação** (`gamification.py`):
```python
class GamificationSystem:
    MAP_UNLOCK_LEVELS = {
        "corridor": 1,
        "curve": 5,
        "circle": 10
    }
    
    @staticmethod
    def is_map_unlocked(map_name, agent_level):
        return agent_level >= MAP_UNLOCK_LEVELS.get(map_name, 1)
```

### Sistema de Upgrades

Cada upgrade custa XP e incrementa um stat:

```python
UPGRADES = {
    "accel": {"custo_xp": 100, "incremento": 0.05},
    "turn_speed": {"custo_xp": 80, "incremento": 0.5},
    "max_speed": {"custo_xp": 150, "incremento": 1.0}
}
```

**Como usar**:
```python
from gamification import GamificationSystem

# Verificar se pode fazer upgrade
can_upgrade, msg = GamificationSystem.can_upgrade(agent_info, "accel")

if can_upgrade:
    GamificationSystem.apply_upgrade(agent_info, "accel")
    print(f"Upgrade aplicado! Novo nível: {agent_info.level}")

# Listar upgrades disponíveis
upgrades = GamificationSystem.get_upgrades_available(agent_info)
```

### Achievements

Sistema de conquistas desbloqueáveis:

```python
ACHIEVEMENTS = {
    "primeiro_checkpoint": "Completar o primeiro checkpoint",
    "perfeito_corridor": "Completar corridor com zero colisões",
    "speedrun": "Completar corrida em menos de 10 segundos",
    "nivel_10": "Atingir nível 10",
    "upgrade_completo": "Maxar todos os upgrades"
}
```

**Verificar**:
```python
from gamification import Achievement

unlocked = Achievement.get_unlocked_achievements(agent_info)
for ach in unlocked:
    print(f"🏆 {ach['nome']}: {ach['descricao']}")
```

---

## Integração com o Main Loop

### Passagem de Stats ao Ambiente

```python
# Em main.py, ao inicializar o ambiente:
env = DummyVecEnv([
    make_env(selected_map, car_stats=agent_info.stats) 
    for _ in range(n_parallel)
])
```

Isso garante que **cada carro no grid tem a física customizada** do agente.

### Atualização de XP e Nível

Ao final de cada episódio:

```python
if dones[idx]:
    xp_gained = max(0, int(score * 10))  # 10 XP por ponto
    agent_info_cache.historico.append({
        "xp_gained": xp_gained,
        "checkpoints": checkpoints_hist[idx][-1],
        "tempo": episode_time,
        "tipo_evento": "simulacao"
    })
    
    # Atualiza nível
    total_xp = sum(h.get('xp_gained', 0) for h in agent_info_cache.historico)
    agent_info_cache.level = GamificationSystem.calculate_level(total_xp)
    
    save_agents(agents_all)  # Persiste mudanças
```

### Exibição no Ranking

O `interface_ranking.py` agora mostra:

```
Pos    Agente|Mapa           Score    Nível    Acel
────────────────────────────────────────────────────
1      PowerBot|corridor     45.32       3      0.60
2      SpeedBot|corridor     38.15       2      0.50
3      BalanceBot|corridor   35.21       2      0.50
```

---

## Arquivos Criados/Modificados

### Novos Arquivos

- **`race_manager.py`** (230 linhas)
  - `RaceResult`: Resultado de corrida
  - `CompetitiveRaceManager`: Gerenciador de torneios

- **`gamification.py`** (210 linhas)
  - `GamificationSystem`: Níveis, upgrades, desbloqueios
  - `Achievement`: Sistema de conquistas

### Arquivos Modificados

- **`interface_agents.py`** (+40 linhas)
  - `AgentInfo.__init__()`: Adicionados `stats` e `level`
  - `AgentInfo.upgrade()`: Método para incrementar stats

- **`environment.py`** (+20 linhas)
  - `CorridaEnv.__init__()`: Parâmetro `car_stats`
  - `CorridaEnv.step()`: Usa stats dinâmicos
  - `MultiAgentEnv`: Suporta `car_stats_list`

- **`main.py`** (+70 linhas)
  - `RaceManager`: Classe para corridas multi-modelos
  - `make_env()`: Aceita `car_stats`
  - Exibição de stats em console

- **`interface_ranking.py`** (+20 linhas)
  - `draw_ranking()`: Mostra nível e aceleração

---

## Casos de Uso

### Caso 1: Evolução de Agente

```
Sessão 1: Agente "MeuBot" nível 1
├─ Treina em corridor
├─ Ganha 500 XP
└─ Sobe para nível 3

Sessão 2: Agente nível 3
├─ Compra upgrade "Melhor Motor" (100 XP)
├─ Aceleração: 0.5 → 0.55
├─ Treina de novo em corridor (mais rápido agora)
├─ Ganha 600 XP (score melhor)
└─ Sobe para nível 5

Sessão 3: Agente nível 5
├─ Mapa "curve" desbloqueado!
├─ Treina em curve
├─ Precisa reaprender com nova física
└─ Evolui como piloto real
```

### Caso 2: Corrida Competitiva

```
python main.py

Menu → Novo Modo: "Corrida Competitiva"
├─ Seleciona 4 melhores agentes
├─ RaceManager carrega modelos
├─ Executa 8 ambientes paralelos em 4 pares
│  ├─ Env 0,4: PowerBot vs SpeedBot (raia 0)
│  ├─ Env 1,5: PowerBot vs BalanceBot (raia 1)
│  ├─ Env 2,6: SpeedBot vs BalanceBot (raia 2)
│  └─ Env 3,7: (repeticão para mais dados)
└─ Exibe ranking em tempo real
```

### Caso 3: Torneio

```python
tournament = CompetitiveRaceManager(map_type="circle")
tournament.load_top_agents()

results, history = tournament.run_tournament(races_per_pair=3)

# Resultado:
# PowerBot: 5 vitórias (campeão)
# BalanceBot: 3 vitórias
# SpeedBot: 1 vitória
```

---

## Impacto para o Portfólio

Essa camada de gamificação eleva o projeto de:

❌ **Antes**: "Agente RL que aprende a andar reto"
✅ **Depois**: "Jogo de gerenciamento de equipe de IA com economia de upgrade"

### Diferenciais Visuais

1. **Diversidade Visual**: Carros com cores diferentes (stats do agente)
2. **Competição Real**: Múltiplos agentes lado a lado em tempo real
3. **Progressão**: XP, níveis, upgrades = engajamento
4. **Desafio Escalável**: Mapas desbloqueados por progresso

### Impacto Técnico

1. **Problema Resolvido**: Múltiplos modelos em paralelo
2. **Arquitetura Limpa**: `RaceManager`, `GamificationSystem` separadas
3. **Extensível**: Fácil adicionar novos upgrades, achievements, mapas
4. **Portfólio**: Demonstra visão de "game design meets RL"

---

## Próximas Melhorias (v2.2)

1. **Interface de Upgrade**
   - Menu visual para comprar upgrades
   - Animação de upgrade (carro brilha, som, etc)

2. **Visualização de Torneios**
   - Tela de bracket (8-agentes em árvore)
   - Placar em tempo real

3. **Trophy Room**
   - Galeria de achievements desbloqueados
   - Histórico de recordes

4. **Curriculum Learning Automático**
   - Sistema seleciona mapas por nível
   - Dificuldade escala com progresso

5. **Modo Campeonato**
   - Multirrodadas (liga)
   - Gráficos de evolução de performance

---

## Conclusão

A **Camada de Gamificação v2.1** transforma o projeto em um **jogo completo com IA**, mantendo a base científica de RL intacta. O sistema é modular, extensível e oferece uma experiência visual impressionante para portfólio.

**Status**: ✅ Implementado e pronto para validação manual
