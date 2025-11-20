"""RewardShaper para design modular de funções de recompensa."""

from abc import ABC, abstractmethod
from typing import Dict, Tuple, Any, Optional
import numpy as np


class BaseRewardShaper(ABC):
    """Interface abstrata para funções de recompensa."""
    
    @abstractmethod
    def compute_reward(self, 
                      position: Tuple[float, float],
                      velocity: float,
                      angle: float,
                      checkpoint_idx: int,
                      total_checkpoints: int,
                      collision: bool,
                      out_of_bounds: bool,
                      progress: float,
                      **kwargs) -> float:
        """Computa recompensa baseada em estado do ambiente.
        
        Args:
            position: (x, y) posição do carro
            velocity: velocidade do carro
            angle: ângulo do carro
            checkpoint_idx: índice do checkpoint atual
            total_checkpoints: total de checkpoints
            collision: se houve colisão
            out_of_bounds: se saiu da pista
            progress: progresso (0 a 1)
            **kwargs: argumentos adicionais
            
        Returns:
            Recompensa em float.
        """
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reseta estado interno do shaper (se necessário)."""
        pass


class BalancedRewardShaper(BaseRewardShaper):
    """Recompensa balanceada: checkpoint + velocidade + penalidades."""
    
    def __init__(self, 
                 checkpoint_reward: float = 100.0,
                 collision_penalty: float = -50.0,
                 speed_reward_factor: float = 0.5,
                 progress_reward_factor: float = 1.0,
                 out_of_bounds_penalty: float = -100.0,
                 stability_reward: float = 1.0):
        """Inicializa RewardShaper balanceado.
        
        Args:
            checkpoint_reward: Recompensa por atingir checkpoint.
            collision_penalty: Penalidade por colisão.
            speed_reward_factor: Fator de recompensa por velocidade.
            progress_reward_factor: Fator de recompensa por progresso.
            out_of_bounds_penalty: Penalidade por sair da pista.
            stability_reward: Recompensa por andar reto.
        """
        self.checkpoint_reward = checkpoint_reward
        self.collision_penalty = collision_penalty
        self.speed_reward_factor = speed_reward_factor
        self.progress_reward_factor = progress_reward_factor
        self.out_of_bounds_penalty = out_of_bounds_penalty
        self.stability_reward = stability_reward
        
        self.last_checkpoint = 0
        self.total_distance = 0.0
    
    def compute_reward(self, 
                      position: Tuple[float, float],
                      velocity: float,
                      angle: float,
                      checkpoint_idx: int,
                      total_checkpoints: int,
                      collision: bool,
                      out_of_bounds: bool,
                      progress: float,
                      last_velocity: Optional[float] = None,
                      **kwargs) -> float:
        """Computa recompensa balanceada."""
        reward = 0.0
        
        # 1. Recompensa por atingir novo checkpoint
        if checkpoint_idx > self.last_checkpoint:
            reward += self.checkpoint_reward * (checkpoint_idx - self.last_checkpoint)
            self.last_checkpoint = checkpoint_idx
        
        # 2. Penalidade por colisão
        if collision:
            reward += self.collision_penalty
        
        # 3. Penalidade por sair da pista
        if out_of_bounds:
            reward += self.out_of_bounds_penalty
        
        # 4. Recompensa por velocidade (não muito rápido, não muito lento)
        speed_bonus = min(velocity / 20.0, 1.0)  # Normaliza até 20 unidades/s
        reward += self.speed_reward_factor * speed_bonus
        
        # 5. Recompensa por progresso
        reward += self.progress_reward_factor * progress
        
        # 6. Recompensa por estabilidade (pouca variação de velocidade)
        if last_velocity is not None:
            stability = 1.0 / (1.0 + abs(velocity - last_velocity))
            reward += self.stability_reward * stability
        
        return reward
    
    def reset(self) -> None:
        """Reseta estado para novo episódio."""
        self.last_checkpoint = 0
        self.total_distance = 0.0


class SpeedRewardShaper(BaseRewardShaper):
    """Recompensa focada em velocidade (racing puro)."""
    
    def __init__(self,
                 speed_reward_factor: float = 2.0,
                 collision_penalty: float = -100.0,
                 checkpoint_bonus: float = 50.0):
        """Inicializa RewardShaper focado em velocidade."""
        self.speed_reward_factor = speed_reward_factor
        self.collision_penalty = collision_penalty
        self.checkpoint_bonus = checkpoint_bonus
        self.last_checkpoint = 0
    
    def compute_reward(self,
                      position: Tuple[float, float],
                      velocity: float,
                      angle: float,
                      checkpoint_idx: int,
                      total_checkpoints: int,
                      collision: bool,
                      out_of_bounds: bool,
                      progress: float,
                      **kwargs) -> float:
        """Computa recompensa focada em velocidade."""
        reward = 0.0
        
        # Recompensa por velocidade (principal)
        reward += self.speed_reward_factor * velocity
        
        # Penalidade por colisão
        if collision:
            reward += self.collision_penalty
        
        # Bônus por checkpoint
        if checkpoint_idx > self.last_checkpoint:
            reward += self.checkpoint_bonus * (checkpoint_idx - self.last_checkpoint)
            self.last_checkpoint = checkpoint_idx
        
        # Penalidade por sair da pista
        if out_of_bounds:
            reward -= 50.0
        
        return reward
    
    def reset(self) -> None:
        """Reseta estado."""
        self.last_checkpoint = 0


class SafetyRewardShaper(BaseRewardShaper):
    """Recompensa focada em segurança e estabilidade."""
    
    def __init__(self,
                 collision_penalty: float = -200.0,
                 out_of_bounds_penalty: float = -150.0,
                 smooth_driving_reward: float = 2.0,
                 checkpoint_bonus: float = 100.0):
        """Inicializa RewardShaper focado em segurança."""
        self.collision_penalty = collision_penalty
        self.out_of_bounds_penalty = out_of_bounds_penalty
        self.smooth_driving_reward = smooth_driving_reward
        self.checkpoint_bonus = checkpoint_bonus
        self.last_checkpoint = 0
    
    def compute_reward(self,
                      position: Tuple[float, float],
                      velocity: float,
                      angle: float,
                      checkpoint_idx: int,
                      total_checkpoints: int,
                      collision: bool,
                      out_of_bounds: bool,
                      progress: float,
                      last_velocity: Optional[float] = None,
                      **kwargs) -> float:
        """Computa recompensa focada em segurança."""
        reward = self.smooth_driving_reward  # Base reward por estar dirigindo
        
        # Penalidades severas
        if collision:
            reward += self.collision_penalty
        
        if out_of_bounds:
            reward += self.out_of_bounds_penalty
        
        # Bônus por checkpoint
        if checkpoint_idx > self.last_checkpoint:
            reward += self.checkpoint_bonus * (checkpoint_idx - self.last_checkpoint)
            self.last_checkpoint = checkpoint_idx
        
        # Recompensa por direção suave
        if last_velocity is not None:
            acceleration = abs(velocity - last_velocity)
            if acceleration < 2.0:  # Aceleração suave
                reward += 1.0
            else:
                reward -= acceleration * 0.5  # Penaliza aceleração brusca
        
        return reward
    
    def reset(self) -> None:
        """Reseta estado."""
        self.last_checkpoint = 0


class RewardShapeFactory:
    """Factory para criar RewardShapers."""
    
    _shapers = {
        'balanced': BalancedRewardShaper,
        'speed': SpeedRewardShaper,
        'safety': SafetyRewardShaper,
    }
    
    @classmethod
    def create(cls, shaper_type: str, **kwargs) -> BaseRewardShaper:
        """Cria RewardShaper pelo tipo.
        
        Args:
            shaper_type: 'balanced', 'speed', 'safety' ou classe customizada.
            **kwargs: Argumentos para o shaper.
            
        Returns:
            Instância de BaseRewardShaper.
            
        Raises:
            ValueError: Se tipo não existir.
        """
        if shaper_type not in cls._shapers:
            raise ValueError(f"Shaper desconhecido: {shaper_type}. "
                           f"Opções: {list(cls._shapers.keys())}")
        
        return cls._shapers[shaper_type](**kwargs)
    
    @classmethod
    def register(cls, name: str, shaper_class: type) -> None:
        """Registra novo RewardShaper customizado.
        
        Args:
            name: Nome do shaper.
            shaper_class: Classe que herda de BaseRewardShaper.
        """
        if not issubclass(shaper_class, BaseRewardShaper):
            raise TypeError(f"{shaper_class} deve herdar de BaseRewardShaper")
        cls._shapers[name] = shaper_class
    
    @classmethod
    def list(cls) -> list:
        """Lista todos os shapers registrados."""
        return list(cls._shapers.keys())
