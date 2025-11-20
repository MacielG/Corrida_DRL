"""Exibição de progresso de fases no CLI."""

from phase_manager import PhaseManager, Phase


def display_phase_progress(agent_name: str):
    """Exibe o progresso detalhado de um agente em CLI.
    
    Args:
        agent_name: Nome do agente
    """
    pm = PhaseManager(agent_name)
    progress = pm.get_phase_progress()
    
    print("\n" + "="*70)
    print(f"📊 PROGRESSO DE {agent_name.upper()}")
    print("="*70)
    
    # Mostra fase atual
    phase = pm.get_current_phase()
    print(f"\n🎯 FASE ATUAL: {phase.id + 1}/4 - {phase.name}")
    print(f"   Mapa: {phase.map_type.upper()}")
    print(f"   {phase.description}")
    
    # Barra de progresso de episódios
    episodes_needed = phase.min_episodes_success
    episodes_done = progress['total_episodes']
    bar_length = 30
    filled = min(episodes_done, episodes_needed)
    bar = "█" * filled + "░" * (episodes_needed - filled)
    print(f"\n📈 Episódios: {episodes_done}/{episodes_needed}")
    print(f"   [{bar}]")
    
    # Taxa de sucesso
    success_rate = progress['recent_success_rate']
    required_rate = progress['success_rate_required']
    bar_length = 20
    filled = int((success_rate / 1.0) * bar_length)
    bar = "▓" * filled + "░" * (bar_length - filled)
    print(f"\n✅ Taxa de Sucesso: {success_rate:.1%} (requer {required_rate:.1%})")
    print(f"   [{bar}]")
    if success_rate >= required_rate:
        print("   ✓ Atingido!")
    
    # Recompensa média
    avg_reward = progress['avg_reward']
    reward_threshold = progress['reward_threshold']
    bar_length = 20
    filled = int((min(avg_reward, reward_threshold) / reward_threshold) * bar_length)
    bar = "▓" * filled + "░" * (bar_length - filled)
    print(f"\n💰 Recompensa Média: {avg_reward:.1f} (requer {reward_threshold:.1f})")
    print(f"   [{bar}]")
    if avg_reward >= reward_threshold:
        print("   ✓ Atingido!")
    
    # Status de conclusão
    print(f"\n{'='*70}")
    if progress['completed']:
        print(f"🎉 FASE COMPLETA! Pronto para avançar.")
    else:
        missing_episodes = max(0, episodes_needed - episodes_done)
        print(f"⏳ Em progresso... Faltam {missing_episodes} episódios bem-sucedidos")
    
    # Mostra todas as fases
    print(f"\n{'='*70}")
    print("📋 TODAS AS FASES:")
    for i, p in enumerate(PhaseManager.PHASES):
        status = "✓" if i < pm.current_phase_id else "→" if i == pm.current_phase_id else "○"
        print(f"  {status} Fase {i+1}: {p.name:20} ({p.map_type:10})")
    
    print("="*70 + "\n")
    
    return progress


def display_all_agents_progress(agents_data: list):
    """Exibe progresso de múltiplos agentes lado a lado.
    
    Args:
        agents_data: Lista de nomes de agentes
    """
    print("\n" + "="*80)
    print("🏆 PROGRESSO GERAL DOS AGENTES")
    print("="*80)
    
    for agent_name in agents_data:
        pm = PhaseManager(agent_name)
        progress = pm.get_phase_progress()
        phase = pm.get_current_phase()
        
        status_icon = "🎉" if progress['completed'] else "⏳"
        success_pct = f"{progress['recent_success_rate']:.0%}"
        
        print(f"{status_icon} {agent_name:15} | Fase {phase.id+1}: {phase.name:15} | Taxa: {success_pct:>4} | Episódios: {progress['total_episodes']:3}")
    
    print("="*80 + "\n")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        agent_name = sys.argv[1]
        display_phase_progress(agent_name)
    else:
        print("Uso: python progress_display.py <agent_name>")
        print("Exemplo: python progress_display.py Bot1")
