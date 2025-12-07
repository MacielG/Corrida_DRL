"""Script para integrar reward_shaper com environment.py

Mostra como usar a arquitetura pronta no core/reward_shaper.py
para tornar recompensas configuráveis.
"""

# ============================================================================
# EXEMPLO DE USO
# ============================================================================

from core.reward_shaper import RewardShapeFactory

# 1. Criar RewardShaper
shaper = RewardShapeFactory.create('balanced', 
    checkpoint_reward=100.0,
    collision_penalty=-50.0,
    speed_reward_factor=0.5,
    progress_reward_factor=1.0,
    out_of_bounds_penalty=-100.0,
    stability_reward=1.0
)

# 2. Em environment.py, no método step():
# OLD (hard-coded):
# reward = 0
# if collision: reward -= 10
# if checkpoint_reached: reward += 8
# ...

# NEW (configurável):
def calculate_reward_with_shaper(shaper, 
                                position, 
                                velocity, 
                                angle,
                                checkpoint_idx,
                                total_checkpoints,
                                collision,
                                out_of_bounds,
                                progress,
                                last_velocity=None):
    """Calcula recompensa usando RewardShaper."""
    reward = shaper.compute_reward(
        position=position,
        velocity=velocity,
        angle=angle,
        checkpoint_idx=checkpoint_idx,
        total_checkpoints=total_checkpoints,
        collision=collision,
        out_of_bounds=out_of_bounds,
        progress=progress,
        last_velocity=last_velocity
    )
    return reward


# ============================================================================
# PATCH para environment.py
# ============================================================================

PATCH_CODE = '''
# No início de environment.py, adicione:
from core.reward_shaper import RewardShapeFactory

class CorridaEnv(gym.Env):
    def __init__(self, ..., reward_shaper_type='balanced', reward_config=None):
        # ... código existente ...
        
        # Inicializa RewardShaper
        config = reward_config or {
            'checkpoint_reward': 100.0,
            'collision_penalty': -50.0,
            'speed_reward_factor': 0.5,
            'progress_reward_factor': 1.0,
            'out_of_bounds_penalty': -100.0,
            'stability_reward': 1.0
        }
        self.reward_shaper = RewardShapeFactory.create(reward_shaper_type, **config)
        self.last_velocity = 0.0
    
    def step(self, action):
        # ... código de ação/física existente ...
        
        # SUBSTITUIR CÁLCULO HARD-CODED DE REWARD por:
        reward = self.reward_shaper.compute_reward(
            position=(self.car1_pos[0], self.car1_pos[1]),
            velocity=self.velocity,
            angle=self.angle,
            checkpoint_idx=self.checkpoint_idx,
            total_checkpoints=len(self.checkpoints),
            collision=collision,
            out_of_bounds=out_of_bounds,
            progress=progress,
            last_velocity=self.last_velocity
        )
        
        self.last_velocity = self.velocity
        
        # ... resto do método ...
    
    def reset(self):
        # ... código existente ...
        self.reward_shaper.reset()
        self.last_velocity = 0.0
        # ...
'''

# ============================================================================
# BENEFÍCIOS
# ============================================================================
"""
✅ Recompensas totalmente configuráveis
✅ Fácil trocar entre 'balanced', 'speed', 'safety'
✅ Suporta reward shaping customizado
✅ Sem duplicação de lógica
✅ Fácil para comparação entre estratégias

EXEMPLO DE CONFIGURAÇÃO:

# Training script
from environment import CorridaEnv
from core.reward_shaper import RewardShapeFactory

# Modo 1: Balanced (default)
env = CorridaEnv(reward_shaper_type='balanced')

# Modo 2: Speed-focused
env = CorridaEnv(reward_shaper_type='speed',
    reward_config={'speed_reward_factor': 3.0})

# Modo 3: Custom
env = CorridaEnv(reward_shaper_type='custom',
    reward_config={
        'checkpoint_reward': 200.0,  # Mais importante
        'collision_penalty': -100.0,  # Mais severo
        'speed_reward_factor': 2.0,
    })

# Usar
obs = env.reset()
for _ in range(1000):
    action = agent.predict(obs)[0]
    obs, reward, done, info = env.step(action)
    if done:
        obs = env.reset()
"""

if __name__ == "__main__":
    # Demonstração
    print("✅ RewardShaper Architecture Ready")
    print("📝 Ver PATCH_CODE acima para integração em environment.py")
    print(f"💡 Shapers disponíveis: {RewardShapeFactory.list()}")
