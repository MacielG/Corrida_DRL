# ⚡ QuickStart - Começar em 5 Minutos

## 1️⃣ Instalação (1 min)

```bash
# Clone
git clone https://github.com/MacielG/Corrida_DRL.git
cd Corrida_DRL

# Ambiente virtual
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows

# Dependências
pip install -r requirements.txt
```

## 2️⃣ Execute o Jogo (3 min)

```bash
python main.py
```

**O que acontece:**
1. Menu principal abre
2. Clique "Assistir Corrida" ou "Treinar"
3. Selecione agente (ou crie um em "Gestão de Agentes")
4. Escolha mapa (Corredor, Curva, Circular)
5. Veja a corrida com dashboard em tempo real

## 3️⃣ Com Configuração Customizada (1 min)

```bash
# Use arquivo de config
cp config_example.yaml meu_config.yaml

# Edite meu_config.yaml com seus parâmetros

# Execute
python main.py --config meu_config.yaml
```

---

## 📊 Monitorar Treinamento

### TensorBoard
```bash
# Terminal 1: Treino
python main.py

# Terminal 2: Visualizar (abra http://localhost:6006)
tensorboard --logdir tensorboard_logs
```

### MLflow
```bash
# Terminal 1
mlflow ui  # Abra http://localhost:5000

# Terminal 2
python main.py
```

---

## 🧪 Rodar Testes

```bash
# Todos
pytest tests/ -v

# Apenas core
pytest tests/test_core_module.py -v

# Com cobertura
pytest --cov=core
```

---

## 📁 Estrutura Básica

```
Corrida_DRL/
├── main.py                 # Ponto de entrada
├── agent.py               # Agente RL
├── environment.py         # Simulador
├── core/                  # Módulos avançados
│   ├── config_manager.py  # Configuração
│   ├── reward_shaper.py   # Recompensas
│   └── callbacks.py       # Monitoramento
├── tests/                 # Testes
├── models/                # Modelos salvos
├── tensorboard_logs/      # TensorBoard
└── config_example.yaml    # Exemplo de config
```

---

## 💡 Próximos Passos

### Trocar Algoritmo
Edite `config_example.yaml`:
```yaml
algorithm:
  name: "PPO"  # ou "SAC"
```

### Trocar Função de Recompensa
```python
from core.reward_shaper import RewardShapeFactory

# Opções: 'balanced', 'speed', 'safety'
shaper = RewardShapeFactory.create('speed')
```

### Usar Melhor Modelo Treinado
```bash
python main.py --skip-training
```

---

## ❓ Troubleshooting

**"ModuleNotFoundError: No module named 'core'"**
→ Certifique-se que você está no diretório `Corrida_DRL`

**"Port 6006 already in use"**
→ TensorBoard rodando em outra janela. Feche ou use porta diferente:
```bash
tensorboard --logdir tensorboard_logs --port 6007
```

**Jogo muito lento**
→ Reduza `n_parallel` em config.yaml (padrão é 4)

---

## 🎯 Exemplo Completo

```bash
# 1. Clone
git clone https://github.com/MacielG/Corrida_DRL.git && cd Corrida_DRL

# 2. Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp config_example.yaml config.yaml
# Edite config.yaml se quiser customizar

# 4. Treino
python main.py --config config.yaml

# 5. Monitore (em outro terminal)
tensorboard --logdir tensorboard_logs

# 6. Abra navegador
# http://localhost:6006
```

**Pronto! Você tem um agente RL treinando em uma pista de corrida com monitoramento em tempo real! 🏎️**

---

## 📚 Saiba Mais

- **README_PRODUCTION.md** - Documentação completa
- **CORRECOES_FLUXO_E_VISUAL.md** - Últimas correções
- **config_example.yaml** - Todos os parâmetros disponíveis

---

**Dúvidas? Abra uma Issue no GitHub! 🐛**
