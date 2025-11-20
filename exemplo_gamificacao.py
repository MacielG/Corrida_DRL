#!/usr/bin/env python3
"""
Exemplo Prático: Sistema de Gamificação em Ação

Este script demonstra como usar a nova camada de gamificação
para criar progressão de agentes, upgrades e corridas competitivas.
"""

from interface_agents import AgentInfo, load_agents, save_agents
from gamification import GamificationSystem, Achievement
from race_manager import CompetitiveRaceManager
from environment import CorridaEnv
import os

def exemplo_1_criar_agente_com_stats():
    """Exemplo 1: Criar agente com stats iniciais"""
    print("\n" + "="*60)
    print("EXEMPLO 1: Criar Agente com Stats")
    print("="*60)
    
    agente = AgentInfo(
        nome="PowerBot",
        tipo="PPO",
        stats={
            "accel": 0.5,
            "turn_speed": 5.0,
            "max_speed": 20.0
        },
        level=1
    )
    
    print(f"Agente criado: {agente.nome}")
    print(f"  Tipo: {agente.tipo}")
    print(f"  Nível: {agente.level}")
    print(f"  Stats:")
    print(f"    - Aceleração: {agente.stats['accel']}")
    print(f"    - Velocidade de Virada: {agente.stats['turn_speed']}°")
    print(f"    - Velocidade Máxima: {agente.stats['max_speed']}")


def exemplo_2_sistema_de_xp_e_niveis():
    """Exemplo 2: Visualizar sistema de XP e níveis"""
    print("\n" + "="*60)
    print("EXEMPLO 2: Sistema de XP e Níveis")
    print("="*60)
    
    # Simula diferentes quantidades de XP
    xp_values = [0, 100, 400, 900, 1600, 2500, 8100]
    
    print("Tabela XP → Nível:")
    print(f"{'XP':<10} {'Nível':<10} {'Próximo Nível':<15}")
    print("-" * 35)
    
    for xp in xp_values:
        nivel = GamificationSystem.calculate_level(xp)
        proxima = GamificationSystem.calculate_next_level_xp(nivel)
        print(f"{xp:<10} {nivel:<10} {proxima:<15}")
    
    # Visualizar progresso
    print("\nProgresso para próximo nível (450 XP total):")
    progress = GamificationSystem.calculate_xp_progress(450)
    bar_length = 20
    bar = "█" * int(bar_length * progress) + "░" * (bar_length - int(bar_length * progress))
    print(f"  [{bar}] {progress*100:.1f}%")


def exemplo_3_desbloqueio_de_mapas():
    """Exemplo 3: Sistema de desbloqueio de mapas"""
    print("\n" + "="*60)
    print("EXEMPLO 3: Desbloqueio de Mapas por Nível")
    print("="*60)
    
    levels_test = [1, 3, 5, 8, 10]
    
    for level in levels_test:
        available = GamificationSystem.get_available_maps(level)
        print(f"\nNível {level}:")
        print(f"  Mapas disponíveis: {', '.join(available)}")
        
        # Verifica cada mapa
        for map_name in ["corridor", "curve", "circle"]:
            is_unlocked = GamificationSystem.is_map_unlocked(map_name, level)
            status = "🔓" if is_unlocked else "🔒"
            print(f"    {status} {map_name}")


def exemplo_4_sistema_de_upgrades():
    """Exemplo 4: Compra e aplicação de upgrades"""
    print("\n" + "="*60)
    print("EXEMPLO 4: Sistema de Upgrades")
    print("="*60)
    
    # Criar agente com XP acumulado
    agente = AgentInfo(nome="SpeedBot", tipo="DQN")
    
    # Simular histórico com XP
    agente.historico = [
        {"xp_gained": 100, "tipo_evento": "treino"},
        {"xp_gained": 150, "tipo_evento": "simulacao"},
        {"xp_gained": 80, "tipo_evento": "simulacao"},
    ]
    
    total_xp = sum(h.get('xp_gained', 0) for h in agente.historico)
    print(f"Agente: {agente.nome}")
    print(f"Total XP: {total_xp}")
    print(f"Nível: {GamificationSystem.calculate_level(total_xp)}")
    
    print("\nUpgrades disponíveis:")
    upgrades = GamificationSystem.get_upgrades_available(agente)
    for upgrade in upgrades:
        status = "✅ Disponível" if upgrade['disponivel'] else "❌ Indisponível"
        print(f"  {upgrade['nome']}: {upgrade['custo_xp']} XP - {status}")
        print(f"    {upgrade['descricao']}")
    
    # Tentar aplicar upgrade
    print("\nAplicando upgrade de Aceleração...")
    can_apply, msg = GamificationSystem.can_upgrade(agente, "accel")
    
    if can_apply:
        success, msg = GamificationSystem.apply_upgrade(agente, "accel")
        print(f"  ✅ {msg}")
        print(f"  Nova aceleração: {agente.stats['accel']}")
        print(f"  Novo nível: {agente.level}")
    else:
        print(f"  ❌ {msg}")


def exemplo_5_achievements():
    """Exemplo 5: Sistema de Achievements"""
    print("\n" + "="*60)
    print("EXEMPLO 5: Sistema de Achievements")
    print("="*60)
    
    agente = AgentInfo(nome="AchievementHunter", tipo="SAC", level=10)
    agente.historico = [
        {"checkpoints": 1, "mapa": "corridor", "tempo": 8.5},  # Speedrun
        {"checkpoints": 2, "mapa": "corridor"},
    ]
    
    print(f"Agente: {agente.nome} (Nível {agente.level})")
    print("\nAchievements desbloqueados:")
    
    unlocked = Achievement.get_unlocked_achievements(agente)
    if unlocked:
        for achievement in unlocked:
            print(f"  🏆 {achievement['nome']}")
            print(f"     {achievement['descricao']}")
    else:
        print("  Nenhum achievement desbloqueado ainda.")


def exemplo_6_corrida_com_diferentes_stats():
    """Exemplo 6: Visualizar diferença de física entre carros"""
    print("\n" + "="*60)
    print("EXEMPLO 6: Corrida com Diferentes Stats")
    print("="*60)
    
    # Criar dois agentes com diferentes stats
    agente1 = AgentInfo("CarroLento", "PPO", stats={"accel": 0.3, "turn_speed": 3.0, "max_speed": 15.0})
    agente2 = AgentInfo("CarroRapido", "DQN", stats={"accel": 0.7, "turn_speed": 8.0, "max_speed": 25.0})
    
    print(f"Agente 1: {agente1.nome}")
    print(f"  Stats: Acel={agente1.stats['accel']}, Turn={agente1.stats['turn_speed']}, MaxSpeed={agente1.stats['max_speed']}")
    
    print(f"\nAgente 2: {agente2.nome}")
    print(f"  Stats: Acel={agente2.stats['accel']}, Turn={agente2.stats['turn_speed']}, MaxSpeed={agente2.stats['max_speed']}")
    
    print("\nComparação:")
    print(f"  Aceleração: {agente1.stats['accel']:.1f} vs {agente2.stats['accel']:.1f} " +
          f"({'2.3x mais rápido' if agente2.stats['accel'] > agente1.stats['accel'] else ''})")
    print(f"  Velocidade: {agente1.stats['max_speed']} vs {agente2.stats['max_speed']} " +
          f"(+{agente2.stats['max_speed'] - agente1.stats['max_speed']} km/h)")
    print(f"  Controle: {agente1.stats['turn_speed']:.1f}° vs {agente2.stats['turn_speed']:.1f}° " +
          f"({'2.7x mais ágil' if agente2.stats['turn_speed'] > agente1.stats['turn_speed'] else ''})")


def exemplo_7_environment_com_stats():
    """Exemplo 7: Criar ambiente com stats customizados"""
    print("\n" + "="*60)
    print("EXEMPLO 7: Ambiente com Physics Customizada")
    print("="*60)
    
    # Ambientes com diferentes stats
    stats_lento = {"accel": 0.3, "turn_speed": 3.0, "max_speed": 15.0}
    stats_rapido = {"accel": 0.8, "turn_speed": 8.0, "max_speed": 28.0}
    
    env_lento = CorridaEnv(map_type="corridor", car_stats=stats_lento)
    env_rapido = CorridaEnv(map_type="corridor", car_stats=stats_rapido)
    
    print(f"Environment Lento:")
    print(f"  ACCEL_FORCE: {env_lento.ACCEL_FORCE}")
    print(f"  TURN_SPEED: {env_lento.TURN_SPEED}")
    print(f"  MAX_SPEED: {env_lento.MAX_SPEED}")
    
    print(f"\nEnvironment Rápido:")
    print(f"  ACCEL_FORCE: {env_rapido.ACCEL_FORCE}")
    print(f"  TURN_SPEED: {env_rapido.TURN_SPEED}")
    print(f"  MAX_SPEED: {env_rapido.MAX_SPEED}")
    
    print("\n✅ Ambientes criados com física diferente!")


def exemplo_8_visualizar_tabela_upgrades():
    """Exemplo 8: Tabela completa de upgrades"""
    print("\n" + "="*60)
    print("EXEMPLO 8: Tabela de Upgrades")
    print("="*60)
    
    upgrades = GamificationSystem.UPGRADES
    
    print(f"{'Upgrade':<20} {'Custo XP':<12} {'Incremento':<12} {'Máximo':<10}")
    print("-" * 54)
    
    for key, config in upgrades.items():
        print(f"{config['nome']:<20} {config['custo_xp']:<12} " +
              f"+{config['incremento']:<11} {config['maximo']:<10}")


def main():
    """Execute todos os exemplos"""
    print("\n" + "[EXEMPLOS] SISTEMA DE GAMIFICACAO CORRIDA DRL v2.1" + "\n")
    
    try:
        exemplo_1_criar_agente_com_stats()
        exemplo_2_sistema_de_xp_e_niveis()
        exemplo_3_desbloqueio_de_mapas()
        exemplo_4_sistema_de_upgrades()
        exemplo_5_achievements()
        exemplo_6_corrida_com_diferentes_stats()
        exemplo_7_environment_com_stats()
        exemplo_8_visualizar_tabela_upgrades()
        
        print("\n" + "="*60)
        print("[OK] TODOS OS EXEMPLOS EXECUTADOS COM SUCESSO!")
        print("="*60)
        print("\nPróximos passos:")
        print("  1. Criar agentes no menu principal")
        print("  2. Treinar agentes para ganhar XP")
        print("  3. Comprar upgrades com XP ganho")
        print("  4. Ver diferença de performance no mapa")
        print("  5. Desbloquear mapas mais difíceis")
        print("  6. Participar de corridas competitivas")
        
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
