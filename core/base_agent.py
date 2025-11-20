"""Classe abstrata BaseAgent para modularidade de algoritmos."""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any, Dict
import os


class BaseAgent(ABC):
    """Interface abstrata para agentes RL."""
    
    @abstractmethod
    def __init__(self, 
                 env: Any,
                 model_path: str = "models/agent",
                 learning_rate: float = 0.0003,
                 gamma: float = 0.98,
                 **kwargs):
        """Inicializa agente.
        
        Args:
            env: Ambiente Gym/Gymnasium.
            model_path: Caminho para salvar/carregar modelo.
            learning_rate: Taxa de aprendizado.
            gamma: Fator de desconto.
            **kwargs: Argumentos específicos do algoritmo.
        """
        self.env = env
        self.model_path = model_path
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.model = None  # Será definido pela subclasse
    
    @abstractmethod
    def train(self, 
              total_timesteps: int = 100000,
              eval_interval: int = 5000,
              callbacks: Optional[list] = None) -> Dict[str, Any]:
        """Treina o agente.
        
        Args:
            total_timesteps: Total de passos de treinamento.
            eval_interval: Intervalo para avaliação.
            callbacks: Lista de callbacks do SB3.
            
        Returns:
            Dicionário com estatísticas de treinamento.
        """
        pass
    
    @abstractmethod
    def predict(self, 
                observation: Any, 
                deterministic: bool = False) -> Tuple[int, Optional[Any]]:
        """Prediz ação baseada em observação.
        
        Args:
            observation: Estado observado.
            deterministic: Se True, usa política determinística.
            
        Returns:
            Tupla (ação, estado_interno_opcional).
        """
        pass
    
    @abstractmethod
    def evaluate(self, 
                 env: Any = None,
                 n_episodes: int = 10,
                 deterministic: bool = True) -> float:
        """Avalia desempenho do agente.
        
        Args:
            env: Ambiente para avaliação (usa self.env se None).
            n_episodes: Número de episódios para avaliar.
            deterministic: Se True, usa política determinística.
            
        Returns:
            Recompensa média.
        """
        pass
    
    def save(self, path: Optional[str] = None) -> None:
        """Salva modelo.
        
        Args:
            path: Caminho para salvar (usa self.model_path se None).
        """
        save_path = path or self.model_path
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        if self.model is not None:
            self.model.save(save_path)
    
    def load(self, path: Optional[str] = None) -> None:
        """Carrega modelo.
        
        Args:
            path: Caminho para carregar (usa self.model_path se None).
        """
        load_path = path or self.model_path
        if os.path.exists(load_path + ".zip"):
            # SB3 adiciona .zip automaticamente
            self._load_model(load_path)
        elif os.path.exists(load_path):
            self._load_model(load_path)
    
    @abstractmethod
    def _load_model(self, path: str) -> None:
        """Carrega modelo (implementado pela subclasse)."""
        pass
    
    def get_policy(self):
        """Retorna política do agente."""
        if self.model is not None:
            return self.model.policy
        return None
    
    def __repr__(self) -> str:
        """Representação em string."""
        return f"{self.__class__.__name__}(model_path={self.model_path}, lr={self.learning_rate})"
