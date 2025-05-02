"""Agente RL e callback de logging para Corrida DRL.

Define a classe Agent para treinar, avaliar e salvar modelos RL, além de LogCallback para métricas customizadas.
"""
from stable_baselines3 import DQN, PPO, SAC
from stable_baselines3.common.callbacks import BaseCallback
import os
from logger import setup_logger
from config import RL_ALGORITHM
import numpy as np

logger = setup_logger()

class CustomCallback(BaseCallback):
    def __init__(self, verbose: int = 0):
        super().__init__(verbose)
    def _on_step(self) -> bool:
        if hasattr(self.training_env, 'get_attr'):
            speeds = self.training_env.get_attr('car1_speed')
            if speeds:
                self.logger.record('metrics/avg_speed', np.mean(speeds))
        return True

class LogCallback(BaseCallback):
    """Callback customizado para logging de recompensas durante o treinamento.

    Args:
        verbose (int): Nível de verbosidade.
    """
    def __init__(self, verbose: int = 0):
        super(LogCallback, self).__init__(verbose)
        self.rewards = []

    def _on_step(self) -> bool:
        """Executa a cada passo do treinamento para registrar recompensas.

        Returns:
            bool: True para continuar o treinamento.
        """
        reward = self.locals.get("rewards", 0)
        self.rewards.append(reward)
        if len(self.rewards) % 1000 == 0:
            avg_reward = sum(self.rewards[-1000:]) / 1000
            logger.info(f"Recompensa média nos últimos 1000 passos: {avg_reward}")
        return True

class Agent:
    """Agente RL para Corrida DRL usando Stable Baselines3 (DQN, PPO, SAC).

    Args:
        env (CorridaEnv ou VecEnv): Ambiente de corrida.
        model_path (str): Caminho para salvar/carregar o modelo.
    """
    def __init__(self, env, model_path: str = "models/model_corridor_car1", learning_rate: float = 0.0003, gamma: float = 0.98, **kwargs):
        self.env = env
        self.model_path = model_path
        algorithms = {"DQN": DQN, "PPO": PPO, "SAC": SAC}
        algo_kwargs = {"learning_rate": learning_rate, "gamma": gamma, "tensorboard_log": None}  # Disable TensorBoard
        if RL_ALGORITHM == "DQN":
            algo_kwargs.update(dict(buffer_size=200000, batch_size=64, exploration_fraction=0.4, target_update_interval=500))
        self.model = algorithms[RL_ALGORITHM]("MlpPolicy", env, verbose=1, **algo_kwargs)

    def train(self, total_timesteps: int = 100000, eval_interval: int = 5000):
        """Treina o agente por um número de passos, salvando checkpoints.

        Args:
            total_timesteps (int): Total de passos de treinamento.
            eval_interval (int): Intervalo para avaliação e salvamento.
        """
        best_score = -float('inf')
        callback = LogCallback(verbose=1)
        custom_callback = CustomCallback()
        for i in range(0, total_timesteps, eval_interval):
            self.model.learn(eval_interval, reset_num_timesteps=False, callback=[callback, custom_callback])
            current_score = self.evaluate(self.env)
            if current_score > best_score:
                self.save(f"{self.model_path}_best")
                best_score = current_score
            self.save(f"{self.model_path}_step_{i+eval_interval}")

    def predict(self, state, deterministic: bool = False) -> int:
        """Prediz a ação do agente dado um estado.

        Args:
            state (np.array): Estado do ambiente.
            deterministic (bool): Se True, usa política determinística.
        Returns:
            int: Ação escolhida.
        """
        action, _ = self.model.predict(state, deterministic=deterministic)
        import numpy as np
        # Garante que a ação sempre será um int, seja escalar ou array
        if isinstance(action, (np.ndarray, list)):
            action = np.asarray(action)
            if action.shape == ():
                return int(action)
            return int(action.flat[0])
        return int(action)

    def evaluate(self, env, n_episodes: int = 10) -> float:
        """Avalia o agente em múltiplos episódios.

        Args:
            env (CorridaEnv ou VecEnv): Ambiente de avaliação.
            n_episodes (int): Número de episódios.
        Returns:
            float: Recompensa média.
        """
        import numpy as np
        total_reward = 0
        for _ in range(n_episodes):
            reset_result = env.reset()
            if isinstance(reset_result, tuple):
                state, info = reset_result
            else:
                state = reset_result
                info = {}
            done = False
            if isinstance(state, (list, np.ndarray)) and hasattr(env, 'envs'):
                state = state[0]
                env_single = env.envs[0]
            else:
                env_single = env
            while not done:
                action = self.predict(state, deterministic=True)
                result = env_single.step(action)
                if len(result) == 5:
                    state, reward, terminated, truncated, _ = result
                    done = terminated or truncated
                else:
                    state, reward, done, _ = result
                total_reward += reward
        return total_reward / n_episodes

    def save(self, path: str = None):
        """Salva o modelo treinado.

        Args:
            path (str): Caminho para salvar.
        """
        if path is None:
            path = self.model_path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.save(path)

    def load(self, path: str):
        """Carrega um modelo treinado.

        Args:
            path (str): Caminho do modelo salvo.
        """
        algorithms = {"DQN": DQN, "PPO": PPO, "SAC": SAC}
        self.model = algorithms[RL_ALGORITHM].load(path, env=self.env)
