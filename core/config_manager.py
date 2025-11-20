"""ConfigManager para gerenciar configurações via YAML/JSON com type hints."""

import json
import yaml
import os
from typing import Any, Dict, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class AlgorithmConfig:
    """Configuração específica de algoritmo RL."""
    name: str  # DQN, PPO, SAC
    learning_rate: float = 0.0003
    gamma: float = 0.98
    batch_size: int = 64
    buffer_size: int = 200000
    exploration_fraction: float = 0.4
    target_update_interval: int = 500
    policy: str = "MlpPolicy"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EnvironmentConfig:
    """Configuração do ambiente de simulação."""
    map_type: str = "corridor"  # corridor, curve, circle
    width: int = 600
    height: int = 400
    max_steps: int = 500
    render: bool = False
    render_interval: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RewardConfig:
    """Configuração da função de recompensa."""
    checkpoint_reward: float = 100.0
    collision_penalty: float = -50.0
    speed_reward_factor: float = 0.5
    progress_reward_factor: float = 1.0
    stability_reward: float = 1.0
    out_of_bounds_penalty: float = -100.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrainingConfig:
    """Configuração de treinamento."""
    total_timesteps: int = 100000
    eval_interval: int = 5000
    n_parallel: int = 4
    n_eval_episodes: int = 10
    checkpoint_interval: int = 5000
    save_best_only: bool = True
    verbose: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LoggingConfig:
    """Configuração de logging e monitoramento."""
    log_dir: str = "logs"
    models_dir: str = "models"
    tensorboard_log: Optional[str] = "tensorboard_logs"
    mlflow_tracking_uri: Optional[str] = None
    mlflow_experiment_name: str = "corrida_drl"
    save_logs: bool = True
    log_level: str = "INFO"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CorrectionConfig:
    """Configuração completa do projeto."""
    algorithm: AlgorithmConfig = field(default_factory=lambda: AlgorithmConfig("DQN"))
    environment: EnvironmentConfig = field(default_factory=EnvironmentConfig)
    reward: RewardConfig = field(default_factory=RewardConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm.to_dict(),
            "environment": self.environment.to_dict(),
            "reward": self.reward.to_dict(),
            "training": self.training.to_dict(),
            "logging": self.logging.to_dict(),
        }


class ConfigManager:
    """Gerenciador de configurações com suporte a YAML e JSON."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Inicializa ConfigManager.
        
        Args:
            config_path: Caminho para arquivo YAML/JSON. Se None, usa defaults.
        """
        self.config: CorrectionConfig = CorrectionConfig()
        
        if config_path and os.path.exists(config_path):
            self.load(config_path)
    
    def load(self, config_path: str) -> None:
        """Carrega configuração de arquivo YAML ou JSON.
        
        Args:
            config_path: Caminho do arquivo.
            
        Raises:
            ValueError: Se arquivo tiver extensão inválida.
            FileNotFoundError: Se arquivo não existir.
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path}")
        
        _, ext = os.path.splitext(config_path)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if ext.lower() == '.yaml' or ext.lower() == '.yml':
                data = yaml.safe_load(f)
            elif ext.lower() == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Formato não suportado: {ext}. Use .yaml ou .json")
        
        self._update_from_dict(data)
    
    def _update_from_dict(self, data: Dict[str, Any]) -> None:
        """Atualiza configuração a partir de dicionário."""
        if not data:
            return
        
        if 'algorithm' in data:
            self.config.algorithm = AlgorithmConfig(**{
                **asdict(self.config.algorithm),
                **data['algorithm']
            })
        
        if 'environment' in data:
            self.config.environment = EnvironmentConfig(**{
                **asdict(self.config.environment),
                **data['environment']
            })
        
        if 'reward' in data:
            self.config.reward = RewardConfig(**{
                **asdict(self.config.reward),
                **data['reward']
            })
        
        if 'training' in data:
            self.config.training = TrainingConfig(**{
                **asdict(self.config.training),
                **data['training']
            })
        
        if 'logging' in data:
            self.config.logging = LoggingConfig(**{
                **asdict(self.config.logging),
                **data['logging']
            })
    
    def save(self, config_path: str, format: str = 'yaml') -> None:
        """Salva configuração em arquivo.
        
        Args:
            config_path: Caminho para salvar.
            format: 'yaml' ou 'json'.
        """
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)
        
        data = self.config.to_dict()
        
        with open(config_path, 'w', encoding='utf-8') as f:
            if format.lower() == 'yaml':
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            elif format.lower() == 'json':
                json.dump(data, f, indent=2)
            else:
                raise ValueError(f"Formato não suportado: {format}")
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """Acesso tipo dicionário com path (ex: 'training.total_timesteps').
        
        Args:
            *keys: Caminho da chave (ex: 'training', 'total_timesteps')
            default: Valor padrão se chave não existir.
            
        Returns:
            Valor da configuração ou default.
        """
        obj = self.config
        for key in keys:
            if hasattr(obj, key):
                obj = getattr(obj, key)
            else:
                return default
        return obj
    
    def update(self, **kwargs) -> None:
        """Atualiza configuração com kwargs.
        
        Exemplo:
            config.update(learning_rate=0.001, total_timesteps=50000)
        """
        # Mapeia kwargs para estrutura aninhada
        updates = {
            'algorithm': {},
            'environment': {},
            'reward': {},
            'training': {},
            'logging': {}
        }
        
        # Mapeamento de top-level para seções
        mappings = {
            # Algorithm
            'learning_rate': ('algorithm', 'learning_rate'),
            'gamma': ('algorithm', 'gamma'),
            'batch_size': ('algorithm', 'batch_size'),
            'policy': ('algorithm', 'policy'),
            # Environment
            'map_type': ('environment', 'map_type'),
            'width': ('environment', 'width'),
            'height': ('environment', 'height'),
            'max_steps': ('environment', 'max_steps'),
            # Training
            'total_timesteps': ('training', 'total_timesteps'),
            'eval_interval': ('training', 'eval_interval'),
            'n_parallel': ('training', 'n_parallel'),
            # Reward
            'checkpoint_reward': ('reward', 'checkpoint_reward'),
            'collision_penalty': ('reward', 'collision_penalty'),
        }
        
        for key, value in kwargs.items():
            if key in mappings:
                section, field = mappings[key]
                updates[section][field] = value
        
        self._update_from_dict(updates)
    
    def __repr__(self) -> str:
        """Representação em string da configuração."""
        import json
        return json.dumps(self.config.to_dict(), indent=2)


# Instância global para fácil acesso
_global_config = ConfigManager()


def get_config() -> ConfigManager:
    """Retorna instância global de ConfigManager."""
    return _global_config


def init_config(config_path: Optional[str] = None) -> ConfigManager:
    """Inicializa configuração global.
    
    Args:
        config_path: Caminho para arquivo de configuração.
        
    Returns:
        Instância de ConfigManager.
    """
    global _global_config
    _global_config = ConfigManager(config_path)
    return _global_config
