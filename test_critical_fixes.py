#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para validar que os erros criticos foram corrigidos.
"""
import os
import sys

def test_imports():
    """Testa se todos os modulos podem ser importados."""
    print("[TEST] Testando importacoes...")
    try:
        from environment import CorridaEnv
        from agent import Agent
        from interface_dpg import InterfaceDPG
        from interface_ranking import load_ranking, save_ranking
        from interface_menu import InterfaceMenu
        from interface_dashboard import Dashboard
        print("  [OK] Todas as importacoes funcionam")
        return True
    except Exception as e:
        print(f"  [ERROR] Erro de importacao: {e}")
        return False

def test_interface_methods():
    """Testa se os metodos faltantes foram implementados."""
    print("[TEST] Testando metodos de interface...")
    try:
        from interface_dpg import InterfaceDPG
        iface = InterfaceDPG(width=800, height=600, n_parallel=2)
        
        # Verifica se metodos existem
        assert hasattr(iface, 'draw_loading'), "draw_loading nao existe"
        assert hasattr(iface, 'draw_env_grid'), "draw_env_grid nao existe"
        assert hasattr(iface, 'draw_env_grid_simple'), "draw_env_grid_simple nao existe"
        assert hasattr(iface, 'draw_car_grid'), "draw_car_grid nao existe"
        
        print("  [OK] Todos os metodos de interface existem")
        iface.close()
        return True
    except Exception as e:
        print(f"  [ERROR] Erro nos metodos: {e}")
        return False

def test_vecenv():
    """Testa se VecEnv.reset() esta sendo tratado corretamente."""
    print("[TEST] Testando VecEnv.reset()...")
    try:
        from environment import CorridaEnv
        from stable_baselines3.common.vec_env import DummyVecEnv
        
        env = DummyVecEnv([lambda: CorridaEnv() for _ in range(2)])
        obs = env.reset()
        
        # DummyVecEnv.reset() deve retornar apenas obs (not tuple)
        assert not isinstance(obs, tuple), f"Expected obs, got tuple: {type(obs)}"
        assert obs.shape[0] == 2, f"Expected 2 observations, got {obs.shape[0]}"
        
        print(f"  [OK] VecEnv.reset() retorna corretamente: shape={obs.shape}")
        env.close()
        return True
    except Exception as e:
        print(f"  [ERROR] Erro em VecEnv: {e}")
        return False

def test_ranking_functions():
    """Testa se as funcoes de ranking existem."""
    print("[TEST] Testando funcoes de ranking...")
    try:
        from interface_ranking import load_ranking, save_ranking
        
        # Test load
        data = load_ranking("test_ranking_temp.json")
        assert isinstance(data, dict), f"load_ranking deve retornar dict, got {type(data)}"
        
        # Test save
        test_data = {"agent1|map1": {"score": 100, "speed": 50, "tempo": 10}}
        save_ranking(test_data, "test_ranking_temp.json")
        
        # Test load again
        loaded = load_ranking("test_ranking_temp.json")
        assert loaded == test_data, "Dados salvo/carregado nao correspondem"
        
        # Cleanup
        if os.path.exists("test_ranking_temp.json"):
            os.remove("test_ranking_temp.json")
        
        print("  [OK] Funcoes de ranking funcionam corretamente")
        return True
    except Exception as e:
        print(f"  [ERROR] Erro em ranking: {e}")
        # Cleanup
        if os.path.exists("test_ranking_temp.json"):
            os.remove("test_ranking_temp.json")
        return False

def test_dashboard():
    """Testa se o dashboard lida com listas vazias."""
    print("[TEST] Testando dashboard...")
    try:
        from interface_dashboard import Dashboard
        import pygame
        
        pygame.init()
        screen = pygame.Surface((1280, 720))
        dashboard = Dashboard(screen, 900, 380, 720)
        
        # Test com listas vazias
        rewards_hist = [[], []]
        collisions_hist = [[], []]
        penalties_hist = [[], []]
        
        # Isso nao deve quebrar
        dashboard.draw_metrics_grid(rewards_hist, collisions_hist, penalties_hist)
        
        print("  [OK] Dashboard lida com listas vazias")
        pygame.quit()
        return True
    except Exception as e:
        print(f"  [ERROR] Erro no dashboard: {e}")
        try:
            pygame.quit()
        except:
            pass
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("VALIDANDO CORRECOES DE ERROS CRITICOS")
    print("="*60 + "\n")
    
    tests = [
        test_imports,
        test_interface_methods,
        test_vecenv,
        test_ranking_functions,
        test_dashboard,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n[ERROR] ERRO INESPERADO EM {test.__name__}: {e}\n")
            results.append(False)
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"RESULTADO: {passed}/{total} testes passaram")
    print("="*60 + "\n")
    
    if passed == total:
        print("[SUCCESS] Todas as correcoes criticas foram validadas com sucesso!")
        sys.exit(0)
    else:
        print("[FAILED] Alguns testes falharam. Verifique acima.")
        sys.exit(1)
