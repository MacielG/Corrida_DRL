# 🚀 Quickstart (5 Minutos)

Comece a usar Corrida DRL em 5 minutos.

---

## 📦 Pré-requisitos

- Python 3.10+
- pip

---

## ⚡ Instalação (2 minutos)

```bash
# 1. Clone ou navigate para o diretório
cd Corrida_DRL

# 2. Instale dependências
pip install -r requirements.txt

# 3. Pronto!
```

---

## 🎮 Seu Primeiro Treino (3 minutos)

```bash
# Execute o script padrão
python main_refactored.py
```

Você verá:
- Treino executando
- Logs em tempo real
- Ranking de agentes ao final
- Arquivo `ranking.json` com resultados

---

## 🎯 Personalize

### Mudar Reward Shaper

```python
from environment import CorridaEnv
from config import EnvironmentConfig

# Opção 1: Speed (máxima velocidade)
config = EnvironmentConfig(reward_shaper_type='speed')
env = CorridaEnv(config)

# Opção 2: Safety (máxima segurança)
config = EnvironmentConfig(reward_shaper_type='safety')
env = CorridaEnv(config)

# Opção 3: Balanced (padrão)
config = EnvironmentConfig(reward_shaper_type='balanced')
env = CorridaEnv(config)
```

### Mudar Mapa

```python
config = EnvironmentConfig(map_type='circle')  # corridor, curve, circle
```

### Mudar Duração

```python
config = EnvironmentConfig(max_timesteps=2000)  # padrão: 1000
```

---

## 📚 Próximos Passos

1. **Leia**: `docs/TUTORIAL.md` (30 minutos)
2. **Estude**: `docs/API.md` (referência)
3. **Execute**: `examples/example_basic_training.py`

---

## ❓ Troubleshooting

### Import error: ModuleNotFoundError

```bash
# Instale novamente
pip install -r requirements.txt --force-reinstall
```

### CUDA not found

```bash
# Não precisa GPU, CPU funciona normalmente
# PyTorch usará CPU automaticamente
```

### Reward muito baixo

```python
# Use 'safety' shaper para treino inicial
env = CorridaEnv(reward_shaper_type='safety')
```

---

## 📊 Ver Resultados

Após executar `python main_refactored.py`:

```bash
# Ver ranking
cat ranking.json

# Ver logs
tail -f logs/training.log
```

---

## 🎓 Aprender Mais

- **Reward Shaping**: `docs/REWARD_SHAPING.md`
- **Loop Detection**: `docs/LOOP_DETECTION.md`
- **API Completa**: `docs/API.md`
- **Exemplos**: `examples/`

---

**Pronto?** Agora leia `docs/TUTORIAL.md` para entender tudo em detalhes!
