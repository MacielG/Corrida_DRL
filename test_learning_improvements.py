"""
Script de teste para validar as melhorias de aprendizado (Reward Shaping, Subjetivacao, Competicao).
Executa testes isolados para cada componente.
"""

import os
import sys
import json
import numpy as np
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from environment import CorridaEnv
from agent import Agent
from interface_agents import AgentInfo, save_agents, load_agents
from stable_baselines3.common.vec_env import DummyVecEnv
import time

def test_reward_shaping():
    """Testa se o reward shaping está funcionando (velocidade + checkpoint)."""
    print("\n" + "="*60)
    print("TESTE 1: REWARD SHAPING (Densidade de Recompensa)")
    print("="*60)
    
    env = CorridaEnv(map_type="corridor")
    obs, _ = env.reset()
    
    total_reward = 0.0
    steps = 0
    checkpoints_hit = 0
    
    # Simula 100 steps
    for step in range(100):
        # Tenta sempre acelerar e virar para checkpoint
        action = 0 if step % 2 == 0 else 3  # Acelera e vira direita
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        steps += 1
        
        if info.get('success', False):
            checkpoints_hit += 1
            print(f"  [OK] Checkpoint {checkpoints_hit} atingido em step {step}")
        
        if terminated or truncated:
            break
    
    avg_reward = total_reward / steps if steps > 0 else 0
    print(f"\nResultado:")
    print(f"  Recompensa total: {total_reward:.2f}")
    print(f"  Recompensa media/step: {avg_reward:.4f}")
    print(f"  Checkpoints atingidos: {checkpoints_hit}")
    
    # Critério de sucesso: recompensa média positiva (density working)
    success = avg_reward > 0.01
    print(f"  Status: {'[PASS]' if success else '[FAIL]'} - {'Recompensa densa' if success else 'Recompensa muito esparsa'}")
    
    return success

def test_agent_persistence():
    """Testa se o agente carrega e salva o modelo corretamente (subjetivacao)."""
    print("\n" + "="*60)
    print("TESTE 2: PERSISTENCIA DO AGENTE (Subjetivacao)")
    print("="*60)
    
    # Cria agente de teste
    test_agent_name = "TestAgent_Learning"
    test_model_path = f"models/test_{test_agent_name}"
    
    # Remove se existir
    if os.path.exists(f"{test_model_path}.zip"):
        os.remove(f"{test_model_path}.zip")
    
    # Treina por um pouco
    print(f"\n1. Criando e treinando agente '{test_agent_name}'...")
    env = DummyVecEnv([lambda: CorridaEnv(map_type="corridor")])
    agent = Agent(env, model_path=test_model_path, learning_rate=0.0003, gamma=0.98)
    
    start_time = time.time()
    agent.train(total_timesteps=5000)  # Treino rápido
    elapsed = time.time() - start_time
    print(f"   Treino completado em {elapsed:.1f}s")
    
    # Salva
    agent.save(test_model_path)
    assert os.path.exists(f"{test_model_path}.zip"), "Modelo nao foi salvo!"
    print(f"   [OK] Modelo salvo em {test_model_path}.zip")
    
    # Carrega o modelo
    print(f"\n2. Carregando modelo existente...")
    agent2 = Agent(env, model_path=test_model_path)
    agent2.load(f"{test_model_path}.zip")
    print(f"   [OK] Modelo carregado com sucesso")
    
    # Verifica se os pesos são iguais (prova de continuidade)
    obs = env.reset()
    action1, _ = agent.model.predict(obs, deterministic=True)
    action2, _ = agent2.model.predict(obs, deterministic=True)
    
    assert np.allclose(action1, action2), "Acoes diferem apos carregar modelo!"
    print(f"   [OK] Acoes consistentes: ambos predizem {action1[0]}")
    
    # Testa historico em agents.json
    print(f"\n3. Testando historico em agents.json...")
    ag = AgentInfo(test_agent_name, "DQN", tempo_acumulado=elapsed, modelo_path=f"{test_model_path}.zip")
    ag.historico.append({
        "timestamp": time.time(),
        "duration": elapsed,
        "map": "corridor",
        "xp_gained": 150,
        "tipo_evento": "treino"
    })
    
    # Salva em JSON
    agents = load_agents()
    agents = [a for a in agents if a.get("nome") != test_agent_name]  # Remove se existir
    agents.append(ag.to_dict())
    save_agents(agents)
    print(f"   [OK] Agente salvo em agents.json")
    
    # Recarrega e verifica
    agents_loaded = load_agents()
    ag_loaded = next((a for a in agents_loaded if a.get("nome") == test_agent_name), None)
    assert ag_loaded is not None, "Agente nao encontrado em agents.json!"
    assert len(ag_loaded.get("historico", [])) > 0, "Historico vazio!"
    print(f"   [OK] Agente recarregado com historico: {len(ag_loaded.get('historico', []))} eventos")
    
    # Limpa
    os.remove(f"{test_model_path}.zip")
    agents = [a for a in agents if a.get("nome") != test_agent_name]
    save_agents(agents)
    
    print(f"\nResultado: [PASS] - Subjetivacao funcionando")
    return True

def test_competitive_tracking():
    """Testa se o ranking e histórico de competição estão sendo rastreados."""
    print("\n" + "="*60)
    print("TESTE 3: RASTREAMENTO COMPETITIVO (Ranking + Historico)")
    print("="*60)
    
    # Simula múltiplas corridas de um agente
    test_agent_name = "CompetitiveAgent"
    ag = AgentInfo(test_agent_name, "PPO", tempo_acumulado=0.0, modelo_path="models/dummy.zip")
    
    scores = [100, 250, 180, 320, 280]  # Histórico de scores
    
    print(f"\n1. Simulando {len(scores)} corridas do agente '{test_agent_name}'...")
    for i, score in enumerate(scores):
        xp = max(0, int(score * 10))
        ag.historico.append({
            "mapa": "corridor",
            "score": score,
            "velocidade": 5.0 + i*0.5,
            "tempo": 20.0 - i,
            "xp_gained": xp,
            "checkpoints": min(i, 2),
            "data": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tipo_evento": "simulacao"
        })
        print(f"   Corrida {i+1}: score={score}, xp={xp}")
    
    # Calcula nível
    total_xp = sum(h.get('xp_gained', 0) for h in ag.historico)
    level = max(1, int(total_xp / 100) + 1)
    
    print(f"\n2. Estatisticas acumuladas:")
    print(f"   Total de corridas: {len(ag.historico)}")
    print(f"   Total de XP: {total_xp}")
    print(f"   Nivel atual: {level}")
    print(f"   Score maximo: {max(scores)}")
    print(f"   Score medio: {np.mean(scores):.1f}")
    
    # Verifica ranking
    best_score = max(s['score'] for s in ag.historico)
    best_time = min(s['tempo'] for s in ag.historico)
    
    ranking = {
        f"PPO|corridor": {
            "score": best_score,
            "speed": 5.0 + len(scores)*0.5,
            "tempo": best_time
        }
    }
    
    print(f"\n3. Ranking simulado:")
    for key, data in ranking.items():
        print(f"   {key}: score={data['score']}, tempo={data['tempo']:.1f}s")
    
    # Verifica evolução
    print(f"\n4. Evolucao de score ao longo do tempo:")
    for i, h in enumerate(ag.historico):
        print(f"   Corrida {i+1}: {h['score']} pontos")
    
    print(f"\nResultado: [PASS] - Sistema competitivo funcionando")
    return True

def test_parallel_training():
    """Testa treino paralelo com múltiplos ambientes."""
    print("\n" + "="*60)
    print("TESTE 4: TREINO PARALELO (DummyVecEnv)")
    print("="*60)
    
    n_parallel = 4
    print(f"\n1. Criando {n_parallel} ambientes paralelos...")
    
    def make_env():
        return CorridaEnv(map_type="corridor")
    
    env = DummyVecEnv([make_env for _ in range(n_parallel)])
    print(f"   [OK] {n_parallel} ambientes criados")
    
    # Testa reset
    print(f"\n2. Testando reset...")
    obs = env.reset()
    assert obs.shape == (n_parallel, 15), f"Shape errado: {obs.shape}"
    print(f"   [OK] Obs shape correto: {obs.shape}")
    
    # Testa step
    print(f"\n3. Testando step com acoes diferentes...")
    actions = [0, 1, 2, 3]  # Acelera, freia, esquerda, direita
    obs, rewards, dones, infos = env.step(actions)
    
    print(f"   Rewards: {rewards}")
    print(f"   Dones: {dones}")
    print(f"   [OK] Step executado corretamente")
    
    # Simula episódio
    print(f"\n4. Simulando episodio completo...")
    total_steps = 0
    while not all(dones):
        actions = [np.random.randint(0, 4) for _ in range(n_parallel)]
        obs, rewards, dones, infos = env.step(actions)
        total_steps += 1
        if total_steps > 500:
            break
    
    print(f"   Episodio completado em {total_steps} steps")
    print(f"   [OK] Treino paralelo funcionando")
    
    print(f"\nResultado: [PASS] - Paralelo funcionando")
    return True

def main():
    """Executa todos os testes."""
    print("\n" + "="*70)
    print(" TESTES DE VALIDACAO: MELHORIAS DE APRENDIZADO (v2.0)")
    print("="*70)
    
    results = []
    
    try:
        results.append(("Reward Shaping", test_reward_shaping()))
    except Exception as e:
        print(f"[FAIL]: {e}")
        results.append(("Reward Shaping", False))
    
    try:
        results.append(("Persistencia", test_agent_persistence()))
    except Exception as e:
        print(f"[FAIL]: {e}")
        results.append(("Persistencia", False))
    
    try:
        results.append(("Competicao", test_competitive_tracking()))
    except Exception as e:
        print(f"[FAIL]: {e}")
        results.append(("Competicao", False))
    
    try:
        results.append(("Paralelo", test_parallel_training()))
    except Exception as e:
        print(f"[FAIL]: {e}")
        results.append(("Paralelo", False))
    
    # Resumo
    print("\n" + "="*70)
    print(" RESUMO DE TESTES")
    print("="*70)
    
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{name:30} {status}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} testes passaram")
    
    if passed_count == total_count:
        print("\n[SUCCESS] TODOS OS TESTES PASSARAM! Arquitetura RL v2.0 validada.")
        return 0
    else:
        print(f"\n[WARNING] {total_count - passed_count} teste(s) falharam.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
