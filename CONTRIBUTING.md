# 🤝 Contribuindo para Corrida DRL

Obrigado por considerar contribuir! Este documento descreve como fazer isso.

## 📋 Índice
1. [Código de Conduta](#código-de-conduta)
2. [Como Contribuir](#como-contribuir)
3. [Desenvolvimento Local](#desenvolvimento-local)
4. [Padrões de Código](#padrões-de-código)
5. [Submeter PR](#submeter-pr)
6. [Reportar Bugs](#reportar-bugs)

---

## 📜 Código de Conduta

Todos os colaboradores devem:
- ✅ Ser respeitosos
- ✅ Incluir diversidade
- ✅ Focar em argumentos, não em pessoas
- ✅ Reportar comportamento inaceitável para os mantenedores

Comportamento abusivo **não é tolerado** e resultará em exclusão.

---

## 💬 Como Contribuir

### Reportar Bugs 🐛

1. **Procure** se alguém já reportou no Issues
2. **Descreva claramente**:
   - Versão do Python e SO
   - Passos para reproduzir
   - Comportamento esperado vs observado
   - Screenshots/logs se relevante

**Exemplo:**
```
Título: PPO falha em treino com n_parallel=8

Versão: Python 3.11, Ubuntu 20.04
Passos:
1. python main.py --config config.yaml (com n_parallel: 8)
2. Selecione PPO
3. Inicie treino

Erro:
RuntimeError: CUDA out of memory

Esperado: Treino com 8 ambientes paralelos
```

### Sugerir Melhorias 💡

1. **Issue com rótulo `enhancement`**
2. **Descreva claramente**:
   - Problema que resolve
   - Solução proposta
   - Exemplos de como seria usado
   - Alternativas consideradas

**Exemplo:**
```
Título: Adicionar suporte a GPU com CUDA

Descrição:
Atual: Treino é apenas em CPU
Proposto: Detectar e usar GPU automaticamente

Impacto: 3-5x speedup em máquinas com GPU
```

### Submeter Código 🚀

1. **Forque o repositório**
2. **Crie branch**: `git checkout -b feature/sua-feature`
3. **Implemente** com testes
4. **Push** e abra PR

---

## 🛠️ Desenvolvimento Local

### Setup

```bash
# Clone seu fork
git clone https://github.com/SEU_USUARIO/Corrida_DRL.git
cd Corrida_DRL

# Crie virtual env
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale em modo desenvolvimento
pip install -e .
pip install -r requirements.txt
pip install pytest pytest-cov flake8 black
```

### Workflow

```bash
# Crie sua branch
git checkout -b feature/minha-feature

# Faça mudanças
# ... edite arquivos ...

# Teste tudo
pytest tests/ -v
flake8 core tests
black core tests

# Commit
git add .
git commit -m "Adiciona minha feature"

# Push
git push origin feature/minha-feature
```

---

## 🎨 Padrões de Código

### Python Style

Seguimos PEP 8 com algumas flexibilidades:

```python
# ✅ Bom
def compute_reward(position: Tuple[float, float], 
                   velocity: float) -> float:
    """Computa recompensa baseada em posição e velocidade."""
    reward = velocity * 0.5
    return reward

# ❌ Ruim
def computeReward(pos,vel):
    return vel*0.5
```

### Type Hints

```python
# ✅ Com type hints
from typing import Dict, Optional, Tuple

def process_data(data: Dict[str, Any], 
                 threshold: Optional[float] = None) -> Tuple[bool, Dict]:
    pass

# ❌ Sem type hints
def process_data(data, threshold=None):
    pass
```

### Docstrings

```python
# ✅ Bom
def train_agent(self, total_timesteps: int = 100000) -> Dict[str, float]:
    """Treina o agente com validação periódica.
    
    Args:
        total_timesteps: Total de passos para treinar.
        
    Returns:
        Dicionário com estatísticas de treinamento:
        - 'final_reward': Recompensa final média
        - 'training_time': Tempo total em segundos
        
    Raises:
        ValueError: Se total_timesteps < 1000.
    """
    pass

# ❌ Ruim
def train_agent(self, total_timesteps):
    # treina
    pass
```

### Testes

```python
# ✅ Teste bem estruturado
class TestRewardShaper:
    """Testes para RewardShaper."""
    
    def test_checkpoint_reward(self):
        """Testa se recompensa de checkpoint é aplicada."""
        shaper = BalancedRewardShaper()
        reward = shaper.compute_reward(
            position=(0, 0),
            velocity=5.0,
            angle=0.0,
            checkpoint_idx=1,
            total_checkpoints=5,
            collision=False,
            out_of_bounds=False,
            progress=0.0
        )
        assert reward > 0

# ❌ Teste fraco
def test_reward():
    r = compute_reward()
    assert r > 0
```

---

## 📝 Submeter PR

### Título
Ser descritivo e conciso:
- ✅ "Adiciona BalancedRewardShaper com checkpoint detection"
- ❌ "Fix"

### Descrição

```markdown
## Descrição
Breve descrição do que faz.

## Tipo de Mudança
- [ ] Bug fix (não quebra funcionalidade)
- [ ] Nova feature (quebra compatibilidade?)
- [ ] Breaking change (explique por quê)
- [ ] Documentação

## Checklist
- [ ] Testes adicionados/atualizados
- [ ] Documentação atualizada
- [ ] Código passa em `flake8`
- [ ] Testes passam em `pytest`
- [ ] Branch está atualizado com `main`

## Teste Manual
Passos para testar:
1. ...
2. ...

## Screenshots (se aplicável)
[Insira imagens]
```

### CI/CD

Seu PR será validado por:
1. ✅ **Pytest** - Testes unitários
2. ✅ **Flake8** - Estilo de código
3. ✅ **Coverage** - Cobertura de testes
4. ✅ **Integration** - Testes de integração

Todos devem passar para merge.

---

## 🎯 Áreas Prontas para Contribuição

### Fácil (Bom para Iniciantes)
- [ ] Adicionar docstrings faltantes
- [ ] Melhorar mensagens de erro
- [ ] Adicionar exemplos no README
- [ ] Traduzir documentação

### Médio
- [ ] Novo RewardShaper customizado
- [ ] Novo tipo de mapa
- [ ] Melhora de performance
- [ ] Mais testes

### Avançado
- [ ] Novo algoritmo RL (A3C, DDPG, etc)
- [ ] Transfer learning
- [ ] Multi-agent competição
- [ ] Integração com novo simulador

---

## 📚 Estrutura para Adicionar Feature

### 1. Novo RewardShaper

```python
# core/reward_shaper.py
class MyRewardShaper(BaseRewardShaper):
    def compute_reward(self, **kwargs) -> float:
        # Sua implementação
        pass
    
    def reset(self) -> None:
        pass

# Registre
RewardShapeFactory.register('my_shaper', MyRewardShaper)
```

### 2. Novo Algoritmo

```python
# agent.py
class MyAgent(BaseAgent):
    def __init__(self, env, ...):
        super().__init__(env, ...)
        self.model = MyAlgorithm(...)  # SB3 ou customizado
    
    def train(self, total_timesteps: int) -> Dict:
        # Implementação
        pass
    
    def predict(self, observation):
        # Implementação
        pass
```

### 3. Novo Mapa

```python
# environment.py
def _setup_map(self):
    if self.map_type == "meu_mapa":
        self.corridor_rect = (...)
        self.barriers = [...]
        self.checkpoints = [...]
```

---

## 🔍 Code Review Process

1. **Dois reviewers** mínimo (incluindo mantenedor)
2. **Feedback construtivo** - focar em código, não em pessoa
3. **Iteração** - author responde comentários
4. **Aprovação** - após todas mudanças aprovadas
5. **Squash merge** - mantém histórico limpo

---

## 📦 Release Process

Versioning: [Semantic Versioning](https://semver.org/)
- MAJOR.MINOR.PATCH (ex: 2.0.1)

Tags:
```bash
git tag v2.0.1
git push origin v2.0.1
```

---

## 📞 Suporte e Contato

- **Issues**: https://github.com/MacielG/Corrida_DRL/issues
- **Discussions**: https://github.com/MacielG/Corrida_DRL/discussions
- **Email**: seu-email@example.com

---

## ✨ Reconhecimento

Contribuidores serão listados em:
- README.md (seção "Contribuidores")
- GitHub Contributors Page
- Release Notes

---

**Obrigado por contribuir! 🎉**

*Última atualização: Novembro 2024*
