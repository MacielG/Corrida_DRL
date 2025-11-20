# Guia Rápido: Novo Fluxo de Agentes

## Resumo das Mudanças

1. **interface_select.py** - Agora mostra agentes reais (do JSON), não algoritmos
2. **interface_dpg.py** - Pista melhorada com grama, asfalto e carros coloridos
3. **main.py** - Redireciona automaticamente se não há agentes

---

## Como Usar

### Primeira Vez (Sem Agentes)

```
1. python main.py
2. Clique "Assistir Corrida"
3. Sistema detecta: nenhum agente
4. Redireciona para "Gestão de Agentes"
5. Clique "Novo Agente"
6. Preencha:
   - Nome: ex "Piloto1"
   - Algoritmo: DQN, PPO ou SAC
7. Clique "Criar"
8. Volte (ESC)
9. Clique novamente "Assistir Corrida"
10. Veja o card do "Piloto1" para seleção
11. Clique no card → Selecione mapa → Corrida!
```

### Com Agentes Já Criados

```
1. python main.py
2. Clique "Assistir Corrida"
3. Vê cards de todos os agentes
   - Nome
   - Algoritmo
   - Nível
   - XP acumulado
4. Clique em um card para selecionar
5. Clique em um mapa (Corredor Reto, Pista Curva, Circular)
6. Corrida começa!
```

---

## Visual Melhorado

### Antes (Feio)
- Grid branco com círculos vermelhos
- Não parecia um jogo

### Depois (Bonito)
- Fundo com grama verde
- Pista de asfalto cinza
- Faixas brancas decorativas
- Carros triangulares coloridos (mostra direção)
- Checkpoints pulsam quando ativos
- Barreiras com borda vermelha/branca

---

## Arquivos Alterados

### interface_select.py (NOVO COMPLETO)
- Remove lista hardcoded [DQN, PPO, SAC]
- Carrega agentes do agents.json
- Mostra cards com informações reais
- Se vazio, mostra mensagem educada

### interface_dpg.py (MÉTODO ATUALIZADO)
Apenas o método `draw_env_grid_simple`:
- Fundo: grama (34, 139, 34)
- Pista: asfalto (50, 50, 50)
- Carros: triângulos coloridos com direção
- Checkpoints: verdes/ciano pulsante

### main.py (VALIDAÇÃO ADICIONADA)
Seção "selecao_agente":
```python
agents_check = load_agents()
if not agents_check:
    interface.change_state("gestao_agentes")
```

---

## Testes Realizados

✓ Módulos importam corretamente
✓ Método draw_selecao_agente existe
✓ Método draw_env_grid_simple existe
✓ Redirecionamento configurado

---

## Dúvidas Frequentes

**P: O que fazer se "Agente não encontrado" ainda aparecer?**
R: Significa que o agente foi deletado do JSON. Crie um novo em "Gestão de Agentes".

**P: Como mudar a cor do meu carro?**
R: A cor é atribuída automaticamente por índice no grid. Primeiro agente = vermelho, segundo = azul, etc.

**P: Por que o checkpoint pulsa?**
R: É feedback visual - indica qual é o próximo alvo a passar.

**P: Posso treinar múltiplos agentes simultaneamente?**
R: Sim! Crie vários em "Gestão" e a corrida mostrará todos correndo juntos.

---

## Comandos Rápidos

```bash
# Testar fluxo completo
python test_flow.py

# Rodar jogo normal
python main.py

# Ver agents.json
cat agents.json
```

---

## Próximas Etapas

- [x] Corrigir lógica de seleção (agentes reais)
- [x] Melhorar visual da pista
- [x] Redirecionamento automático
- [ ] Adicionar sons
- [ ] Replay de corridas
- [ ] Stats em tempo real
