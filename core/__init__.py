"""Core module para infraestrutura modular."""

from .config_manager import ConfigManager, init_config, get_config
from .reward_shaper import BaseRewardShaper, RewardShapeFactory
from .reward_shaper import BalancedRewardShaper, SpeedRewardShaper, SafetyRewardShaper
from .base_agent import BaseAgent
from .callbacks import TensorBoardCallback, MLflowCallback, EvaluationCallback, MetricsCallback

__all__ = [
    'ConfigManager',
    'init_config',
    'get_config',
    'BaseRewardShaper',
    'RewardShapeFactory',
    'BalancedRewardShaper',
    'SpeedRewardShaper',
    'SafetyRewardShaper',
    'BaseAgent',
    'TensorBoardCallback',
    'MLflowCallback',
    'EvaluationCallback',
    'MetricsCallback',
]
