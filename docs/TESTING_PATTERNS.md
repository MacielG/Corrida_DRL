# Padrões de Testing e Mocking - Corrida_DRL

## Índice
1. [Estrutura de Testes](#estrutura-de-testes)
2. [Fixtures Compartilhadas](#fixtures-compartilhadas)
3. [Padrões de Mocking](#padrões-de-mocking)
4. [Boas Práticas](#boas-práticas)
5. [Exemplos Práticos](#exemplos-práticos)

---

## Estrutura de Testes

### Localização
```
tests/
├── conftest.py                          # Fixtures compartilhadas
├── utils.py                             # Utilidades de teste
├── test_core_module.py                  # Testes do módulo core
├── test_environment.py                  # Testes de ambiente e agente
├── test_interface.py                    # Testes da interface
├── test_interface_modules.py            # Testes de submódulos UI
├── test_integration.py                  # Testes de integração E2E
├── test_main.py                         # Testes do script principal
├── test_reward_shaper_integration.py    # Testes de reward system
├── test_learning.py                     # Testes de aprendizado (slow)
└── test_smoke.py                        # Testes de sanidade rápidos
```

### Nomes de Testes
```python
# ✅ BOM: Descritivo e específico
def test_agent_learning_improves_over_episodes():
def test_reward_shaper_penalizes_collisions():
def test_interface_state_changes_correctly():

# ❌ EVITAR: Genérico ou vago
def test_agent():
def test_reward():
def test_interface():
```

---

## Fixtures Compartilhadas

### Arquivo: conftest.py

#### 1. Fixture: `interface`
```python
@pytest.fixture
def interface():
    """Cria uma interface pygame para testes."""
    pygame.init()
    interface = InterfaceDPG(width=800, height=600, fase_desc="Test", n_parallel=2)
    yield interface
    interface.close()
```

**Uso:**
```python
def test_draw_corridor(interface):
    interface.draw_corridor((100, 200, 600, 200))
    assert interface.screen is not None
```

**Escopo:** Função (criado/destruído a cada teste)

---

#### 2. Fixture: `temp_agents_file`
```python
@pytest.fixture
def temp_agents_file(tmp_path):
    """Cria arquivo temporário com dados de agentes."""
    agents_data = [
        {"id": 1, "nome": "Agente Test 1", "algoritmo": "DQN", ...},
        {"id": 2, "nome": "Agente Test 2", "algoritmo": "PPO", ...}
    ]
    agents_file = tmp_path / "agents_test.json"
    with open(agents_file, 'w') as f:
        json.dump(agents_data, f)
    yield str(agents_file)
    if agents_file.exists():
        agents_file.unlink()
```

**Uso:**
```python
def test_load_agents(temp_agents_file):
    agents = load_agents(temp_agents_file)
    assert len(agents) == 2
```

---

## Padrões de Mocking

### 1. Mock de Funções Simples

```python
def test_agent_training(monkeypatch):
    """Mock de funções que fazem operações pesadas."""
    
    # Mock: previne chamada real a learn()
    monkeypatch.setattr(agent.model, "learn", lambda *a, **k: None)
    
    # Executa teste sem overhead
    agent.train(total_timesteps=1)
    
    # Verifica chamada (opcional)
    assert agent.model.learn.called
```

### 2. Mock de Classes Inteiras

```python
from unittest.mock import Mock

def test_interface_events(monkeypatch):
    """Mock de classe inteira para testes isolados."""
    
    mock_interface = Mock()
    mock_interface.paused = False
    mock_interface.state = "menu"
    mock_interface.change_state = Mock()
    
    # Usar mock no teste
    interface.change_state("simulacao")
    mock_interface.change_state.assert_called_with("simulacao")
```

### 3. Mock com Side Effects

```python
def test_environment_error_handling(monkeypatch):
    """Mock que simula comportamento específico."""
    
    def mock_reset_raises(*args, **kwargs):
        raise RuntimeError("Init failed")
    
    monkeypatch.setattr(CorridaEnv, "reset", mock_reset_raises)
    
    with pytest.raises(RuntimeError, match="Init failed"):
        env.reset()
```

### 4. Mock de Retorno de Função

```python
def test_agent_evaluation(monkeypatch):
    """Mock que controla valor de retorno."""
    
    scores = [10.5, 11.2, 9.8]
    score_iter = iter(scores)
    
    # Cada chamada retorna próximo valor
    monkeypatch.setattr(
        agent, 
        "evaluate", 
        lambda env, n_episodes: next(score_iter)
    )
    
    assert agent.evaluate(env, 2) == 10.5
    assert agent.evaluate(env, 2) == 11.2
```

---

## Boas Práticas

### ✅ O Que Fazer

#### 1. Use Fixtures para Setup/Teardown
```python
# ✅ BOM
@pytest.fixture
def env():
    e = CorridaEnv(map_type="corridor")
    yield e
    e.close()  # Limpeza garantida

def test_env_step(env):
    state, reward, done, _, info = env.step(0)
    assert isinstance(state, np.ndarray)
```

#### 2. Mock Apenas o Necessário
```python
# ✅ BOM: Mock mínimo
def test_agent_prediction(monkeypatch):
    monkeypatch.setattr(agent, "model", Mock(predict=lambda s: 0))
    action = agent.predict(state)
    assert action == 0

# ❌ EVITAR: Mock excessivo
def test_agent_prediction(monkeypatch):
    monkeypatch.setattr("builtins.__import__", lambda: ...)  # Não faça isso!
```

#### 3. Use `parametrize` para Variações
```python
# ✅ BOM: Testa múltiplos casos
@pytest.mark.parametrize("algo", ["DQN", "PPO", "SAC"])
def test_agent_initialization(algo):
    agent = Agent(env, algorithm=algo)
    assert agent.algorithm == algo

# ❌ EVITAR: Múltiplos testes identicos
def test_agent_dqn():
    agent = Agent(env, algorithm="DQN")
    assert agent.algorithm == "DQN"

def test_agent_ppo():
    agent = Agent(env, algorithm="PPO")
    assert agent.algorithm == "PPO"
```

#### 4. Assertions Específicas
```python
# ✅ BOM
def test_checkpoint_detection():
    reward = shaper.compute_reward(
        checkpoint_idx=1,
        collision=False,
        ...
    )
    assert reward > 0, "Reaching checkpoint should give positive reward"

# ❌ EVITAR
def test_checkpoint_detection():
    reward = shaper.compute_reward(checkpoint_idx=1, ...)
    assert reward  # Muito vago!
```

#### 5. Marque Testes Lentos
```python
# ✅ BOM
@pytest.mark.slow
def test_agent_learning_complete_curriculum():
    # Teste que leva 5+ minutos
    pass

# Executa com: pytest -m "not slow"
```

---

### ❌ O Que Evitar

#### 1. Testes Acoplados a Implementação
```python
# ❌ EVITAR
def test_agent():
    # Testa implementação interna
    assert len(agent.experience_buffer) == 32  # Número mágico!
    assert agent._internal_counter == 5

# ✅ BOM
def test_agent_learns():
    # Testa comportamento observável
    initial_score = agent.evaluate(env)
    agent.train(total_timesteps=100)
    final_score = agent.evaluate(env)
    assert final_score >= initial_score - 0.1  # Tolerância
```

#### 2. Testes com Dependências Externas
```python
# ❌ EVITAR
def test_network_call():
    response = requests.get("https://api.example.com")  # Depende de internet!
    assert response.status_code == 200

# ✅ BOM
def test_network_call(monkeypatch):
    mock_response = Mock(status_code=200)
    monkeypatch.setattr(requests, "get", lambda url: mock_response)
    response = requests.get("https://api.example.com")
    assert response.status_code == 200
```

#### 3. Testes que Modificam Estado Global
```python
# ❌ EVITAR
def test_config():
    config.LEARNING_RATE = 0.001  # Afeta testes subsequentes!
    assert config.LEARNING_RATE == 0.001

# ✅ BOM
def test_config(monkeypatch):
    monkeypatch.setattr("config.LEARNING_RATE", 0.001)
    assert config.LEARNING_RATE == 0.001  # Revertido após teste
```

---

## Exemplos Práticos

### Exemplo 1: Teste de Agente com Mocking

```python
def test_agent_training_progression(tmp_path, monkeypatch):
    """Testa que agente treina e melhora score."""
    
    # Setup
    model_path = str(tmp_path / "test_model")
    env = DummyVecEnv([lambda: CorridaEnv(map_type="corridor")])
    agent = Agent(env, model_path=model_path)
    
    # Mock: Previne I/O de disco
    monkeypatch.setattr(agent, "save", lambda path=None: None)
    monkeypatch.setattr(agent, "load", lambda path: None)
    
    # Test: Avalia antes e depois do treino
    initial_score = agent.evaluate(env, n_episodes=3)
    agent.train(total_timesteps=100, eval_interval=50)
    final_score = agent.evaluate(env, n_episodes=3)
    
    # Assert: Ambos devem ser válidos
    assert np.isfinite(initial_score), "Initial score should be finite"
    assert np.isfinite(final_score), "Final score should be finite"
    assert isinstance(initial_score, float), "Score should be float"
```

### Exemplo 2: Teste de Interface com Eventos

```python
def test_interface_event_handling(monkeypatch):
    """Testa processamento de eventos da interface."""
    
    pygame.init()
    interface = InterfaceDPG(width=800, height=600, n_parallel=1)
    
    try:
        # Mock: Simula input do mouse
        monkeypatch.setattr(
            pygame.mouse, 
            "get_pos", 
            lambda: (400, 300)
        )
        
        # Test: Processa evento
        button_rect = pygame.Rect(390, 290, 20, 20)
        mouse_pos = pygame.mouse.get_pos()
        
        assert button_rect.collidepoint(mouse_pos), "Mouse should collide with button"
        
    finally:
        interface.close()
```

### Exemplo 3: Teste de Integração Completa

```python
@pytest.mark.timeout(30)
def test_full_training_cycle(tmp_path, monkeypatch):
    """Testa ciclo completo: criar env, agent, treinar, avaliar."""
    
    # 1. Setup
    env = DummyVecEnv([lambda: CorridaEnv(map_type="corridor")])
    agent = Agent(env, model_path=str(tmp_path / "model"))
    
    # 2. Mock operações pesadas
    monkeypatch.setattr(agent, "save", lambda path=None: None)
    
    # 3. Execute ciclo
    for phase in range(3):
        agent.train(total_timesteps=50, eval_interval=25)
        score = agent.evaluate(env, n_episodes=2)
        
        # Validate
        assert np.isfinite(score), f"Phase {phase}: Score not finite"
    
    # 4. Cleanup
    env.close()
```

---

## Executando Testes

### Comandos Úteis

```bash
# Executar todos os testes rápidos
pytest tests/ -m "not slow" -v

# Executar teste específico
pytest tests/test_environment.py::test_agent_learning -v

# Com cobertura
pytest tests/ --cov=core --cov=agent --cov-report=html

# Modo watch (executa ao salvar)
ptw tests/ -- -m "not slow"

# Apenas testes que falharam
pytest --lf tests/

# Mostrar output de print()
pytest tests/ -s -v

# Timeout para evitar travamentos
pytest tests/ --timeout=30
```

---

## Troubleshooting

### Problema: "pygame.error: No available video device"
**Solução:** Usar headless mode em CI/CD
```python
# conftest.py
import os
if os.getenv("CI"):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
```

### Problema: Fixture não encontrada
**Solução:** Certifique-se que conftest.py está na pasta tests/
```
tests/
├── conftest.py  ← Deve estar aqui
└── test_*.py
```

### Problema: Mock não funciona
**Solução:** Mock antes de usar, não depois
```python
# ❌ ERRADO
agent = Agent(env)
monkeypatch.setattr(agent.model, "learn", lambda *a: None)

# ✅ CORRETO
monkeypatch.setattr(Agent, "model", Mock())
agent = Agent(env)
```

---

## Referências

- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-timeout](https://pytest-timeout.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

---

**Última atualização:** 2025-12-07
**Maintainers:** Amp Team
