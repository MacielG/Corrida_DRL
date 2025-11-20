# Guia Rápido - Corrida DRL v2.0
## Arquitetura RL Científica com Subjetivação

---

## RESUMO DAS MUDANÇAS

Três pilares foram implementados:

### 1. APRENDIZADO GARANTIDO (Reward Shaping)
- Recompensa aumentada por velocidade: `reward += (speed/20.0) * 0.1`
- Penalidade por tempo: `reward -= 0.005` (incentiva terminar rápido)
- Checkpoint massiço: `reward += 20.0` (antes era 12)
- Bônus por completar: `reward += 50.0`

**Resultado**: Agentes aprendem a CORRER, não ficar parados.

### 2. SUBJETIVAÇÃO (Salvando Progresso Individual)
- Cada agente tem um `.zip` único que é CARREGADO antes de treinar
- Histórico persistido em `agents.json` com XP, checkpoints, velocidade
- Sistema de Níveis baseado em XP (1 nível a cada 100 XP)

**Resultado**: Agentes evoluem entre sessões, ganham "vida" virtual.

### 3. COMPETIÇÃO (Rastreamento de Ranking)
- Ranking persistido em `ranking.json` (melhor score por agente/mapa)
- Histórico de corridas salvo (últimas 30 para não pesar)
- Exibição de Nível no menu de agentes

**Resultado**: Agentes competem, interface mostra evolução.

---

## COMO USAR

### Fluxo 1: Criar e Treinar um Agente

```
1. Executar: python main.py
2. Menu inicial → "Gestão de Agentes"
3. Clicar "Novo Agente"
4. Preencher nome (ex: "AlphaDQN") e tipo (DQN/PPO/SAC)
5. Agente criado com modelo vazio
6. Clicar "Train" → Inicia treino offline
   - Treina por 20k passos em 4 ambientes paralelos
   - Salva modelo no arquivo .zip
   - Incrementa XP e atualiza histórico
7. Ao terminar → Agente está pronto para correr
```

### Fluxo 2: Competir com Agentes

```
1. Menu inicial → "Selecionar Agente"
2. Escolher agente treinado
3. Escolher mapa (corridor/curve/circle)
4. Interface exibe:
   - Grade com 8 agentes correndo em paralelo
   - Recompensas em tempo real
   - Dashboard com métricas
5. Ao fim de cada corrida:
   - Score é calculado
   - XP é adicionado (score * 10)
   - Histórico é atualizado
   - Ranking é verificado
```

### Fluxo 3: Visualizar Evolução

```
1. Menu inicial → "Gestão de Agentes"
2. Cada agente mostra:
   - Nome e Tipo de RL
   - Tempo total acumulado
   - Nível (baseado em XP)
   - Status (Treinado ou Novo)
3. Clicar na linha do agente para ver detalhes histórico
```

---

## ARQUIVOS MODIFICADOS

### ✓ `environment.py`
- Aumentou recompensas de checkpoint (12 → 20, +50 ao terminar)
- Adicionou recompensa densa de velocidade
- Adicionou penalidade temporal

### ✓ `interface_agents.py`
- Expandiu `treinar_agente()` para carregar modelo existente
- Adicionou suporte a paralelização (DummyVecEnv com 4 envs)
- Adicionou cálculo de XP no histórico
- Adicionou exibição de Nível no menu

### ✓ `main.py`
- Carrega agentes UMA VEZ (cache de memória)
- Atualiza cache durante episódios
- Salva apenas ao fim do episódio (não mais a cada iteração)
- Adiciona XP baseado em score

### ✓ NOVO: `ARQUITETURA_RL_CIENTIFICA.md`
- Documentação completa das mudanças
- Justificativas científicas
- Métricas antes/depois
- Próximas melhorias sugeridas

### ✓ NOVO: `test_learning_improvements.py`
- 4 testes automatizados validando:
  - Reward Shaping (recompensa densa funciona)
  - Persistência (carregamento de modelos)
  - Competição (ranking + histórico)
  - Paralelização (DummyVecEnv)

---

## ESTRUTURA DE DADOS

### `agents.json`
```json
[
  {
    "nome": "AlphaDQN",
    "tipo": "DQN",
    "tempo_acumulado": 345.2,
    "modelo_path": "models/AlphaDQN_DQN.zip",
    "cor": [120, 180, 255],
    "historico": [
      {
        "timestamp": 1700000000,
        "duration": 50.5,
        "map": "corridor",
        "xp_gained": 500,
        "tipo_evento": "treino"
      },
      {
        "mapa": "corridor",
        "score": 250.5,
        "velocidade": 5.8,
        "tempo": 18.3,
        "xp_gained": 2505,
        "checkpoints": 2,
        "data": "2025-11-20 12:30:45",
        "tipo_evento": "simulacao"
      }
    ]
  }
]
```

### `ranking.json`
```json
{
  "DQN|corridor": {
    "score": 325.8,
    "speed": 6.2,
    "tempo": 17.5
  },
  "PPO|curve": {
    "score": 410.2,
    "speed": 7.1,
    "tempo": 22.3
  }
}
```

---

## CONFIGURAÇÕES RECOMENDADAS

Em `config.py`, ajuste conforme necessário:

```python
# Reward Shaping
REWARD_SCHEME = "dense"  # Use sempre "dense"

# Física do carro
ACCEL_FORCE = 0.5        # Aceleração
FRICTION = 0.98          # Realismo de momentum

# Limites de episódio
MAX_STEPS = 1000         # Steps máximos
MAX_EPISODE_TIME = 120.0 # 120 segundos máximo

# RL
RL_ALGORITHM = "DQN"     # Pode ser: DQN, PPO, SAC
# Em treinar_agente():
# learning_rate = 0.0003  # Taxa de aprendizado
# gamma = 0.98            # Desconto futuro
```

---

## MÉTRICAS ESPERADAS (Após Implementação)

| Métrica | Expectativa |
|---------|------------|
| Recompensa média/episódio | +20 a +60 |
| Velocidade média do carro | 4-8 (escala 0-20) |
| Checkpoints atingidos/episódio | 1-3+ |
| FPS da interface | 55-60 (estável) |
| Tempo de treino 20k steps | 1-3 minutos |
| Progresso persistente | SIM (carrega modelo anterior) |

---

## TROUBLESHOOTING

### ❌ "Agente não aprende"
- Verifique `REWARD_SCHEME = "dense"` em config.py
- Aumente recompensa de checkpoint em environment.py se necessário

### ❌ "Interface trava"
- Reduz `n_parallel` em main.py (8 → 4)
- Verifica se `load_agents()` está FORA do loop principal

### ❌ "Modelo não carrega"
- Verifique se `models/` diretório existe
- Verifique `.zip` path em agents.json é válido

### ❌ "XP não aumenta"
- Verifique se score é calculado corretamente
- XP = score * 10 (veja main.py linha ~330)

---

## PRÓXIMAS MELHORIAS

1. **Curriculum Learning**: Progressão de dificuldade automática
2. **Multi-Agent Racing**: 2+ agentes correndo simultaneamente
3. **Transfer Learning**: Treinar em um mapa → adaptar para outro
4. **Visualização Gráfica**: Gráficos de evolução em tempo real
5. **Replay Memory**: Salvar vídeos das melhores corridas
6. **Distributed Training**: Treinar em múltiplas GPUs/máquinas

---

## VALIDAÇÃO

Todos os testes passaram (4/4):

```
[PASS] Reward Shaping       - Recompensas densas funcionam
[PASS] Persistencia         - Agentes carregam e salvam modelos
[PASS] Competicao           - Ranking + histórico rastreiam evolução
[PASS] Paralelo             - DummyVecEnv com 4-8 ambientes
```

Execute para validar:
```bash
python test_learning_improvements.py
```

---

## REFERÊNCIA DE CÓDIGO CHAVE

### Carregar modelo ao treinar (subjetivação)
```python
# Em treinar_agente()
if os.path.exists(ag.modelo_path):
    agent.load(ag.modelo_path)  # Carrega cérebro anterior
```

### Cálculo de XP durante simulação
```python
# Em main.py loop
xp_gained = max(0, int(score * 10))
agent_info_cache.historico.append({
    "xp_gained": xp_gained,
    "score": score,
    # ... outros campos
})
```

### Exibição de Nível no menu
```python
# Em interface_agents.py
total_xp = sum(h.get('xp_gained', 0) for h in ag.get('historico', []))
level = max(1, int(total_xp / 100) + 1)
```

---

**Versão**: 2.0  
**Data**: 2025-11-20  
**Status**: ✓ Validado (4/4 testes)  
**Mantém compatibilidade**: Sim, com novas features opcionais
