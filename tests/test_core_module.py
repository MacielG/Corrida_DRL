"""Testes para módulo core."""

import pytest
import os
import tempfile
import json
import yaml
from pathlib import Path

from core.config_manager import (
    ConfigManager, AlgorithmConfig, EnvironmentConfig,
    RewardConfig, TrainingConfig, LoggingConfig, CorrectionConfig
)
from core.reward_shaper import (
    BaseRewardShaper, BalancedRewardShaper, SpeedRewardShaper,
    SafetyRewardShaper, RewardShapeFactory
)


class TestConfigManager:
    """Testes para ConfigManager."""
    
    def test_default_config(self):
        """Testa configuração padrão."""
        config = ConfigManager()
        assert config.config.algorithm.name == "DQN"
        assert config.config.environment.map_type == "corridor"
        assert config.config.training.total_timesteps == 100000
    
    def test_load_yaml_config(self):
        """Testa carregamento de arquivo YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'algorithm': {'name': 'PPO', 'learning_rate': 0.001},
                'training': {'total_timesteps': 50000}
            }, f)
            temp_path = f.name
        
        try:
            config = ConfigManager(temp_path)
            assert config.config.algorithm.name == "PPO"
            assert config.config.algorithm.learning_rate == 0.001
            assert config.config.training.total_timesteps == 50000
        finally:
            os.unlink(temp_path)
    
    def test_load_json_config(self):
        """Testa carregamento de arquivo JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'algorithm': {'name': 'SAC'},
                'environment': {'max_steps': 1000}
            }, f)
            temp_path = f.name
        
        try:
            config = ConfigManager(temp_path)
            assert config.config.algorithm.name == "SAC"
            assert config.config.environment.max_steps == 1000
        finally:
            os.unlink(temp_path)
    
    def test_save_config(self):
        """Testa salvar configuração."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ConfigManager()
            config.config.algorithm.learning_rate = 0.002
            
            yaml_path = os.path.join(tmpdir, 'config.yaml')
            config.save(yaml_path, format='yaml')
            
            assert os.path.exists(yaml_path)
            
            # Carrega de volta
            loaded = ConfigManager(yaml_path)
            assert loaded.config.algorithm.learning_rate == 0.002
    
    def test_update_config(self):
        """Testa atualização de configuração."""
        config = ConfigManager()
        config.update(learning_rate=0.005, total_timesteps=200000)
        
        assert config.config.algorithm.learning_rate == 0.005
        assert config.config.training.total_timesteps == 200000
    
    def test_get_nested_config(self):
        """Testa acesso aninhado a configuração."""
        config = ConfigManager()
        
        assert config.get('algorithm', 'name') == 'DQN'
        assert config.get('training', 'total_timesteps') == 100000
        assert config.get('nonexistent', default='fallback') == 'fallback'


class TestRewardShaper:
    """Testes para RewardShaper."""
    
    def test_balanced_reward_shaper(self):
        """Testa BalancedRewardShaper."""
        shaper = BalancedRewardShaper()
        
        # Teste de checkpoint
        reward = shaper.compute_reward(
            position=(0, 0),
            velocity=5.0,
            angle=0.0,
            checkpoint_idx=1,
            total_checkpoints=5,
            collision=False,
            out_of_bounds=False,
            progress=0.2
        )
        
        assert reward > 0  # Deve ter recompensa positiva
    
    def test_collision_penalty(self):
        """Testa penalidade de colisão."""
        shaper = BalancedRewardShaper(collision_penalty=-100.0)
        
        reward = shaper.compute_reward(
            position=(0, 0),
            velocity=5.0,
            angle=0.0,
            checkpoint_idx=0,
            total_checkpoints=5,
            collision=True,
            out_of_bounds=False,
            progress=0.0
        )
        
        assert reward < 0  # Deve ser penalizado
    
    def test_speed_reward_shaper(self):
        """Testa SpeedRewardShaper."""
        shaper = SpeedRewardShaper(speed_reward_factor=2.0)
        
        reward_fast = shaper.compute_reward(
            position=(0, 0),
            velocity=20.0,
            angle=0.0,
            checkpoint_idx=0,
            total_checkpoints=5,
            collision=False,
            out_of_bounds=False,
            progress=0.0
        )
        
        reward_slow = shaper.compute_reward(
            position=(0, 0),
            velocity=5.0,
            angle=0.0,
            checkpoint_idx=0,
            total_checkpoints=5,
            collision=False,
            out_of_bounds=False,
            progress=0.0
        )
        
        assert reward_fast > reward_slow  # Mais rápido deve ter mais recompensa
    
    def test_safety_reward_shaper(self):
        """Testa SafetyRewardShaper."""
        shaper = SafetyRewardShaper()
        
        # Sem colisão
        reward_safe = shaper.compute_reward(
            position=(0, 0),
            velocity=5.0,
            angle=0.0,
            checkpoint_idx=0,
            total_checkpoints=5,
            collision=False,
            out_of_bounds=False,
            progress=0.0
        )
        
        # Com colisão
        reward_crash = shaper.compute_reward(
            position=(0, 0),
            velocity=5.0,
            angle=0.0,
            checkpoint_idx=0,
            total_checkpoints=5,
            collision=True,
            out_of_bounds=False,
            progress=0.0
        )
        
        assert reward_safe > reward_crash
    
    def test_reward_shaper_factory(self):
        """Testa RewardShapeFactory."""
        shapers = RewardShapeFactory.list()
        assert 'balanced' in shapers
        assert 'speed' in shapers
        assert 'safety' in shapers
        
        # Testa criação
        shaper = RewardShapeFactory.create('balanced')
        assert isinstance(shaper, BalancedRewardShaper)
        
        # Testa erro para tipo desconhecido
        with pytest.raises(ValueError):
            RewardShapeFactory.create('unknown')
    
    def test_shaper_reset(self):
        """Testa reset de shaper."""
        shaper = BalancedRewardShaper()
        
        # Primeiro episódio
        reward1 = shaper.compute_reward(
            position=(0, 0),
            velocity=5.0,
            angle=0.0,
            checkpoint_idx=1,
            total_checkpoints=5,
            collision=False,
            out_of_bounds=False,
            progress=0.0
        )
        
        assert shaper.last_checkpoint == 1
        
        shaper.reset()
        assert shaper.last_checkpoint == 0


class TestAlgorithmConfig:
    """Testes para AlgorithmConfig."""
    
    def test_algorithm_config_defaults(self):
        """Testa valores padrão de AlgorithmConfig."""
        config = AlgorithmConfig(name="DQN")
        assert config.learning_rate == 0.0003
        assert config.gamma == 0.98
        assert config.buffer_size == 200000
    
    def test_algorithm_config_to_dict(self):
        """Testa conversão para dicionário."""
        config = AlgorithmConfig(name="PPO", learning_rate=0.001)
        d = config.to_dict()
        
        assert d['name'] == "PPO"
        assert d['learning_rate'] == 0.001
        assert d['gamma'] == 0.98


class TestEnvironmentConfig:
    """Testes para EnvironmentConfig."""
    
    def test_environment_config_defaults(self):
        """Testa valores padrão de EnvironmentConfig."""
        config = EnvironmentConfig()
        assert config.map_type == "corridor"
        assert config.width == 600
        assert config.height == 400
    
    def test_environment_config_custom(self):
        """Testa EnvironmentConfig customizado."""
        config = EnvironmentConfig(map_type="circle", width=800)
        assert config.map_type == "circle"
        assert config.width == 800
        assert config.height == 400


class TestTrainingConfig:
    """Testes para TrainingConfig."""
    
    def test_training_config_defaults(self):
        """Testa valores padrão de TrainingConfig."""
        config = TrainingConfig()
        assert config.total_timesteps == 100000
        assert config.n_parallel == 4
        assert config.save_best_only is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
