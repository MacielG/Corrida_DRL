"""Sistema de gerenciamento de fases com critérios de progresso.

Define as fases de aprendizado e critérios de sucesso/falha para progressão.
"""
from dataclasses import dataclass
from typing import Dict, List
import json
import os

@dataclass
class Phase:
    """Define uma fase de treinamento."""
    id: int
    name: str
    map_type: str
    description: str
    min_episodes_success: int = 5  # Episódios bem-sucedidos necessários
    success_rate_threshold: float = 0.6  # Taxa de sucesso mínima (60%)
    max_episode_steps: int = 1000
    max_episode_time: float = 15.0
    reward_threshold: float = 50.0  # Recompensa mínima acumulada para "pass"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'map_type': self.map_type,
            'description': self.description,
            'min_episodes_success': self.min_episodes_success,
            'success_rate_threshold': self.success_rate_threshold,
            'max_episode_steps': self.max_episode_steps,
            'max_episode_time': self.max_episode_time,
            'reward_threshold': self.reward_threshold,
        }

class PhaseManager:
    """Gerencia progressão entre fases de aprendizado."""
    
    # Fases pré-definidas
    PHASES = [
        Phase(
            id=0,
            name="Iniciante",
            map_type="corridor",
            description="Corredor reto simples - aprender o básico",
            min_episodes_success=5,
            success_rate_threshold=0.6,
            max_episode_steps=1000,
            max_episode_time=20.0,
            reward_threshold=40.0,
        ),
        Phase(
            id=1,
            name="Intermediário",
            map_type="corridor",
            description="Corredor reto - aumentar velocidade",
            min_episodes_success=7,
            success_rate_threshold=0.65,
            max_episode_steps=1000,
            max_episode_time=15.0,
            reward_threshold=60.0,
        ),
        Phase(
            id=2,
            name="Avançado",
            map_type="curve",
            description="Curva - navegação com viragens",
            min_episodes_success=10,
            success_rate_threshold=0.7,
            max_episode_steps=1000,
            max_episode_time=20.0,
            reward_threshold=80.0,
        ),
        Phase(
            id=3,
            name="Maestria",
            map_type="circle",
            description="Circuito completo - máxima dificuldade",
            min_episodes_success=15,
            success_rate_threshold=0.75,
            max_episode_steps=1000,
            max_episode_time=25.0,
            reward_threshold=100.0,
        ),
    ]
    
    def __init__(self, agent_name: str):
        """
        Args:
            agent_name: Nome do agente para persistência de progresso
        """
        self.agent_name = agent_name
        self.current_phase_id = 0
        self.episode_stats = []  # Lista de (phase_id, reward, success, steps)
        self.load_progress()
    
    def load_progress(self):
        """Carrega progresso salvo do agente."""
        progress_file = f"models/{self.agent_name}_progress.json"
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r') as f:
                    data = json.load(f)
                    self.current_phase_id = data.get('current_phase_id', 0)
                    self.episode_stats = data.get('episode_stats', [])
            except Exception as e:
                print(f"[PhaseManager] Erro ao carregar progresso: {e}")
    
    def save_progress(self):
        """Salva progresso do agente."""
        progress_file = f"models/{self.agent_name}_progress.json"
        os.makedirs(os.path.dirname(progress_file) or '.', exist_ok=True)
        try:
            with open(progress_file, 'w') as f:
                json.dump({
                    'current_phase_id': self.current_phase_id,
                    'episode_stats': self.episode_stats,
                }, f, indent=2)
        except Exception as e:
            print(f"[PhaseManager] Erro ao salvar progresso: {e}")
    
    def record_episode(self, reward: float, success: bool, steps: int):
        """Registra resultado de um episódio.
        
        Args:
            reward: Recompensa total acumulada
            success: Se o agente completou com sucesso
            steps: Número de steps no episódio
        """
        self.episode_stats.append({
            'phase_id': self.current_phase_id,
            'reward': reward,
            'success': success,
            'steps': steps,
        })
        self.save_progress()
    
    def get_current_phase(self) -> Phase:
        """Retorna a fase atual."""
        if self.current_phase_id >= len(self.PHASES):
            return self.PHASES[-1]
        return self.PHASES[self.current_phase_id]
    
    def check_phase_completion(self) -> bool:
        """Verifica se a fase atual foi completada.
        
        Retorna True se:
        - Mínimo de episódios bem-sucedidos atingido
        - Taxa de sucesso acima do threshold
        """
        phase = self.get_current_phase()
        
        # Pega estatísticas da fase atual
        current_phase_stats = [
            s for s in self.episode_stats 
            if s['phase_id'] == self.current_phase_id
        ]
        
        if len(current_phase_stats) < phase.min_episodes_success:
            return False
        
        # Últimos N episódios (janela deslizante)
        recent_stats = current_phase_stats[-phase.min_episodes_success:]
        success_count = sum(1 for s in recent_stats if s['success'])
        success_rate = success_count / len(recent_stats)
        
        avg_reward = sum(s['reward'] for s in recent_stats) / len(recent_stats)
        
        return (
            success_rate >= phase.success_rate_threshold and
            avg_reward >= phase.reward_threshold
        )
    
    def advance_phase(self) -> bool:
        """Avança para a próxima fase.
        
        Retorna True se avançou, False se já está na última fase.
        """
        if self.current_phase_id >= len(self.PHASES) - 1:
            return False
        
        self.current_phase_id += 1
        self.save_progress()
        print(f"\n[PhaseManager] ✓ {self.agent_name} AVANÇOU para: {self.get_current_phase().name}")
        return True
    
    def get_phase_progress(self) -> Dict:
        """Retorna progresso detalhado da fase atual."""
        phase = self.get_current_phase()
        current_phase_stats = [
            s for s in self.episode_stats 
            if s['phase_id'] == self.current_phase_id
        ]
        
        recent_stats = current_phase_stats[-phase.min_episodes_success:] if current_phase_stats else []
        success_count = sum(1 for s in recent_stats if s['success'])
        success_rate = success_count / len(recent_stats) if recent_stats else 0
        avg_reward = sum(s['reward'] for s in recent_stats) / len(recent_stats) if recent_stats else 0
        
        return {
            'phase_name': phase.name,
            'total_episodes': len(current_phase_stats),
            'recent_success_rate': success_rate,
            'success_rate_required': phase.success_rate_threshold,
            'avg_reward': avg_reward,
            'reward_threshold': phase.reward_threshold,
            'episodes_needed': phase.min_episodes_success,
            'completed': self.check_phase_completion(),
        }


if __name__ == '__main__':
    # Teste
    pm = PhaseManager('test_agent')
    
    # Simula alguns episódios
    for i in range(10):
        reward = 50 + i*5 if i % 2 == 0 else 40 + i*3
        success = i > 3  # Sucesso depois de 3 episódios
        pm.record_episode(reward, success, 500)
    
    # Verifica progresso
    progress = pm.get_phase_progress()
    print(f"Progresso: {progress}")
    
    # Tenta avançar
    if pm.check_phase_completion():
        pm.advance_phase()
