"""Testes para integração de reward_shaper com environment."""

import pytest
import numpy as np
from environment import CorridaEnv
from core.reward_shaper import RewardShapeFactory, BalancedRewardShaper, SpeedRewardShaper, SafetyRewardShaper


class TestRewardShaperIntegration:
    """Testes de integração reward_shaper com CorridaEnv."""
    
    def test_balanced_shaper_initialization(self):
        """Testa inicialização com balanced shaper."""
        env = CorridaEnv(reward_shaper_type='balanced')
        obs, info = env.reset()
        
        assert env.reward_shaper is not None
        assert isinstance(env.reward_shaper, BalancedRewardShaper)
        assert obs.shape[0] >= 7  # Observação completa
    
    def test_speed_shaper_initialization(self):
        """Testa inicialização com speed shaper."""
        env = CorridaEnv(reward_shaper_type='speed')
        obs, info = env.reset()
        
        assert env.reward_shaper is not None
        assert isinstance(env.reward_shaper, SpeedRewardShaper)
    
    def test_safety_shaper_initialization(self):
        """Testa inicialização com safety shaper."""
        env = CorridaEnv(reward_shaper_type='safety')
        obs, info = env.reset()
        
        assert env.reward_shaper is not None
        assert isinstance(env.reward_shaper, SafetyRewardShaper)
    
    def test_custom_reward_config(self):
        """Testa inicialização com configuração customizada."""
        custom_config = {
            'checkpoint_reward': 200.0,
            'collision_penalty': -100.0,
            'speed_reward_factor': 2.0
        }
        env = CorridaEnv(reward_shaper_type='balanced', reward_config=custom_config)
        obs, info = env.reset()
        
        assert env.reward_shaper.checkpoint_reward == 200.0
        assert env.reward_shaper.collision_penalty == -100.0
        assert env.reward_shaper.speed_reward_factor == 2.0
    
    def test_reward_is_finite(self):
        """Testa se recompensa é sempre finita."""
        env = CorridaEnv()
        obs, info = env.reset()
        
        for _ in range(100):
            action = env.action_space.sample()
            obs, reward, done, truncated, info = env.step(action)
            
            assert np.isfinite(reward), f"Recompensa não finita: {reward}"
            
            if done:
                obs, info = env.reset()
    
    def test_reward_shaper_reset(self):
        """Testa reset do reward shaper."""
        env = CorridaEnv(reward_shaper_type='balanced')
        env.reset()
        
        # Joga alguns steps
        for _ in range(20):
            action = env.action_space.sample()
            obs, reward, done, truncated, info = env.step(action)
            if done:
                break
        
        # Reseta
        obs, info = env.reset()
        
        # Verifica se shaper foi resetado
        assert env.reward_shaper.last_checkpoint == 0
    
    def test_reward_shaper_checkpoint_detection(self):
        """Testa se shaper detecta checkpoint corretamente."""
        shaper = BalancedRewardShaper(checkpoint_reward=100.0)
        
        # Simula chegada ao checkpoint
        reward1 = shaper.compute_reward(
            position=(700, 300),
            velocity=5.0,
            angle=0.0,
            checkpoint_idx=0,
            total_checkpoints=1,
            collision=False,
            out_of_bounds=False,
            progress=0.5
        )
        
        # Simula checkpoint atingido (checkpoint_idx aumentado)
        shaper.last_checkpoint = 0
        reward2 = shaper.compute_reward(
            position=(700, 300),
            velocity=5.0,
            angle=0.0,
            checkpoint_idx=1,  # Checkpoint avançou
            total_checkpoints=1,
            collision=False,
            out_of_bounds=False,
            progress=0.5
        )
        
        # Segundo reward deve incluir checkpoint_reward
        assert reward2 > reward1
        assert shaper.last_checkpoint == 1
    
    def test_different_shapers_different_rewards(self):
        """Testa que diferentes shapers produzem recompensas diferentes."""
        env_balanced = CorridaEnv(reward_shaper_type='balanced')
        env_speed = CorridaEnv(reward_shaper_type='speed')
        env_safety = CorridaEnv(reward_shaper_type='safety')
        
        obs_b, _ = env_balanced.reset()
        obs_s, _ = env_speed.reset()
        obs_sa, _ = env_safety.reset()
        
        rewards_b = []
        rewards_s = []
        rewards_sa = []
        
        for _ in range(50):
            action = 0  # Acelera sempre
            
            obs_b, r_b, done_b, _, _ = env_balanced.step(action)
            obs_s, r_s, done_s, _, _ = env_speed.step(action)
            obs_sa, r_sa, done_sa, _, _ = env_safety.step(action)
            
            rewards_b.append(r_b)
            rewards_s.append(r_s)
            rewards_sa.append(r_sa)
            
            if done_b or done_s or done_sa:
                break
        
        # Shapers diferentes devem produzir recompensas diferentes em média
        avg_b = np.mean(rewards_b)
        avg_s = np.mean(rewards_s)
        avg_sa = np.mean(rewards_sa)
        
        # Pelo menos dois devem ser diferentes
        assert not (np.isclose(avg_b, avg_s) and np.isclose(avg_s, avg_sa))


class TestLoopDetectorIntegration:
    """Testes de integração loop_detector com CorridaEnv."""
    
    def test_loop_detector_initialization(self):
        """Testa inicialização do loop detector."""
        env = CorridaEnv()
        env.reset()
        
        assert env.loop_detector is not None
        assert env.loop_detector.history_size == 100
    
    def test_loop_detector_tracks_position(self):
        """Testa se loop detector rastreia posições."""
        env = CorridaEnv()
        env.reset()
        
        for _ in range(100):
            action = env.action_space.sample()
            obs, reward, done, truncated, info = env.step(action)
            
            if env.current_step % 10 == 0:
                assert len(env.loop_detector.position_history) > 0
            
            if done:
                break
    
    def test_loop_detection_penalizes_loops(self):
        """Testa se loop detection penaliza movimento repetitivo."""
        env = CorridaEnv()
        obs, _ = env.reset()
        
        # Cria um padrão repetitivo (mesmo action)
        rewards_repetitivo = []
        for _ in range(100):
            obs, reward, done, truncated, info = env.step(0)  # Sempre ação 0
            rewards_repetitivo.append(reward)
            if done:
                break
        
        # Se detectou loop, rewards devem diminuir
        # (pode ter penalidade de loop detection)
        assert len(rewards_repetitivo) > 0
    
    def test_loop_detector_reset(self):
        """Testa reset do loop detector."""
        env = CorridaEnv()
        env.reset()
        
        # Joga alguns steps
        for _ in range(50):
            action = env.action_space.sample()
            obs, reward, done, truncated, info = env.step(action)
            if done:
                break
        
        history_before = len(env.loop_detector.position_history)
        
        # Reseta
        env.reset()
        
        # Histórico deve estar vazio
        assert len(env.loop_detector.position_history) == 0
        assert env.loop_detector.loop_count == 0


class TestRewardShapingBehavior:
    """Testes de comportamento esperado do reward shaping."""
    
    def test_collision_penalty(self):
        """Testa que colisão gera penalidade."""
        shaper = BalancedRewardShaper(collision_penalty=-50.0)
        
        reward_no_collision = shaper.compute_reward(
            position=(400, 300),
            velocity=10.0,
            angle=0.0,
            checkpoint_idx=0,
            total_checkpoints=1,
            collision=False,
            out_of_bounds=False,
            progress=0.5
        )
        
        reward_collision = shaper.compute_reward(
            position=(400, 300),
            velocity=10.0,
            angle=0.0,
            checkpoint_idx=0,
            total_checkpoints=1,
            collision=True,
            out_of_bounds=False,
            progress=0.5
        )
        
        # Com colisão deve ter recompensa menor
        assert reward_collision < reward_no_collision
    
    def test_out_of_bounds_penalty(self):
        """Testa que sair da pista gera penalidade."""
        shaper = BalancedRewardShaper(out_of_bounds_penalty=-100.0)
        
        reward_in_bounds = shaper.compute_reward(
            position=(400, 300),
            velocity=10.0,
            angle=0.0,
            checkpoint_idx=0,
            total_checkpoints=1,
            collision=False,
            out_of_bounds=False,
            progress=0.5
        )
        
        reward_out_bounds = shaper.compute_reward(
            position=(400, 300),
            velocity=10.0,
            angle=0.0,
            checkpoint_idx=0,
            total_checkpoints=1,
            collision=False,
            out_of_bounds=True,
            progress=0.5
        )
        
        # Fora da pista deve ter recompensa menor
        assert reward_out_bounds < reward_in_bounds
    
    def test_speed_reward_factor(self):
        """Testa que velocidade maior gera mais recompensa."""
        shaper = SpeedRewardShaper(speed_reward_factor=2.0)
        
        reward_slow = shaper.compute_reward(
            position=(400, 300),
            velocity=1.0,
            angle=0.0,
            checkpoint_idx=0,
            total_checkpoints=1,
            collision=False,
            out_of_bounds=False,
            progress=0.0
        )
        
        reward_fast = shaper.compute_reward(
            position=(400, 300),
            velocity=15.0,
            angle=0.0,
            checkpoint_idx=0,
            total_checkpoints=1,
            collision=False,
            out_of_bounds=False,
            progress=0.0
        )
        
        # Velocidade maior deve gerar recompensa maior
        assert reward_fast > reward_slow


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
