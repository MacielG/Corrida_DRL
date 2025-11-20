"""Callbacks avançados para TensorBoard e MLflow."""

import numpy as np
import os
from typing import Optional, Dict, Any
from stable_baselines3.common.callbacks import BaseCallback
import logging

logger = logging.getLogger(__name__)


class TensorBoardCallback(BaseCallback):
    """Callback para TensorBoard com métricas customizadas."""
    
    def __init__(self, 
                 log_dir: str = "tensorboard_logs",
                 eval_interval: int = 1000,
                 verbose: int = 0):
        """Inicializa TensorBoardCallback.
        
        Args:
            log_dir: Diretório para logs do TensorBoard.
            eval_interval: Intervalo de avaliação.
            verbose: Nível de verbosidade.
        """
        super().__init__(verbose)
        self.log_dir = log_dir
        self.eval_interval = eval_interval
        self.eval_count = 0
        self.episode_count = 0
        self.episode_rewards = []
        self.episode_lengths = []
        
        os.makedirs(log_dir, exist_ok=True)
    
    def _on_step(self) -> bool:
        """Executa a cada passo."""
        # Registra recompensa e comprimento do episódio
        if self.locals.get("done", False):
            self.episode_count += 1
            if "episode" in self.locals:
                ep_info = self.locals["episode"]
                self.logger.record("episode/length", ep_info.get("l", 0))
                self.logger.record("episode/reward", ep_info.get("r", 0))
        
        return True


class MLflowCallback(BaseCallback):
    """Callback para integração com MLflow."""
    
    def __init__(self,
                 experiment_name: str = "corrida_drl",
                 tracking_uri: Optional[str] = None,
                 eval_interval: int = 1000,
                 verbose: int = 0):
        """Inicializa MLflowCallback.
        
        Args:
            experiment_name: Nome do experimento no MLflow.
            tracking_uri: URI do servidor MLflow.
            eval_interval: Intervalo de avaliação.
            verbose: Nível de verbosidade.
        """
        super().__init__(verbose)
        self.experiment_name = experiment_name
        self.tracking_uri = tracking_uri
        self.eval_interval = eval_interval
        self.eval_count = 0
        
        try:
            import mlflow
            self.mlflow = mlflow
            
            if tracking_uri:
                mlflow.set_tracking_uri(tracking_uri)
            
            mlflow.set_experiment(experiment_name)
            mlflow.start_run()
            
            self.run_id = mlflow.active_run().info.run_id
            if self.verbose > 0:
                logger.info(f"MLflow Run ID: {self.run_id}")
        
        except ImportError:
            logger.warning("MLflow não instalado. Callback desabilitado.")
            self.mlflow = None
    
    def _on_step(self) -> bool:
        """Executa a cada passo."""
        if self.mlflow is None:
            return True
        
        # Registra recompensas em tempo real
        if self.locals.get("done", False):
            self.eval_count += 1
            if "episode" in self.locals:
                ep_info = self.locals["episode"]
                reward = ep_info.get("r", 0)
                length = ep_info.get("l", 0)
                
                self.mlflow.log_metrics({
                    "episode/reward": reward,
                    "episode/length": length,
                    "total_timesteps": self.num_timesteps,
                }, step=self.eval_count)
        
        return True
    
    def __del__(self):
        """Finaliza run do MLflow."""
        if self.mlflow is not None:
            try:
                self.mlflow.end_run()
            except Exception as e:
                logger.warning(f"Erro ao finalizar MLflow: {e}")


class EvaluationCallback(BaseCallback):
    """Callback para avaliação periódica durante treinamento."""
    
    def __init__(self,
                 eval_env: Any,
                 eval_interval: int = 5000,
                 n_eval_episodes: int = 10,
                 best_model_save_path: Optional[str] = None,
                 save_best_only: bool = True,
                 verbose: int = 0):
        """Inicializa EvaluationCallback.
        
        Args:
            eval_env: Ambiente para avaliação.
            eval_interval: Intervalo de avaliação.
            n_eval_episodes: Número de episódios para avaliar.
            best_model_save_path: Caminho para salvar melhor modelo.
            save_best_only: Se True, salva apenas melhor modelo.
            verbose: Nível de verbosidade.
        """
        super().__init__(verbose)
        self.eval_env = eval_env
        self.eval_interval = eval_interval
        self.n_eval_episodes = n_eval_episodes
        self.best_model_save_path = best_model_save_path
        self.save_best_only = save_best_only
        self.best_mean_reward = -np.inf
        self.eval_count = 0
    
    def _on_step(self) -> bool:
        """Executa a cada passo."""
        if self.n_calls % self.eval_interval == 0:
            self.eval_count += 1
            
            # Avalia modelo
            mean_reward, std_reward = self._evaluate()
            
            if self.verbose > 0:
                logger.info(
                    f"Avaliação #{self.eval_count} - "
                    f"Recompensa média: {mean_reward:.2f} +/- {std_reward:.2f}"
                )
            
            # Log no TensorBoard
            self.logger.record("eval/mean_reward", mean_reward)
            self.logger.record("eval/std_reward", std_reward)
            
            # Salva melhor modelo
            if self.best_model_save_path is not None:
                if mean_reward > self.best_mean_reward:
                    self.best_mean_reward = mean_reward
                    
                    if self.verbose > 0:
                        logger.info(
                            f"Novo melhor modelo! "
                            f"Recompensa: {mean_reward:.2f}"
                        )
                    
                    self.model.save(self.best_model_save_path)
                
                elif not self.save_best_only:
                    self.model.save(
                        f"{self.best_model_save_path}_step_{self.num_timesteps}"
                    )
        
        return True
    
    def _evaluate(self) -> tuple:
        """Avalia modelo no ambiente de teste."""
        episode_rewards = []
        
        for _ in range(self.n_eval_episodes):
            obs, _ = self.eval_env.reset()
            done = False
            episode_reward = 0.0
            
            while not done:
                action, _ = self.model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, _ = self.eval_env.step(action)
                done = terminated or truncated
                episode_reward += reward
            
            episode_rewards.append(episode_reward)
        
        return np.mean(episode_rewards), np.std(episode_rewards)


class MetricsCallback(BaseCallback):
    """Callback para coleta de métricas detalhadas."""
    
    def __init__(self,
                 collect_fps: bool = True,
                 collect_policy_entropy: bool = True,
                 verbose: int = 0):
        """Inicializa MetricsCallback.
        
        Args:
            collect_fps: Coleta frames por segundo.
            collect_policy_entropy: Coleta entropia da política.
            verbose: Nível de verbosidade.
        """
        super().__init__(verbose)
        self.collect_fps = collect_fps
        self.collect_policy_entropy = collect_policy_entropy
        self.last_time = None
    
    def _on_step(self) -> bool:
        """Executa a cada passo."""
        import time
        
        # FPS
        if self.collect_fps:
            current_time = time.time()
            if self.last_time is None:
                self.last_time = current_time
            else:
                fps = 1.0 / (current_time - self.last_time)
                self.logger.record("metrics/fps", fps)
                self.last_time = current_time
        
        # Policy entropy
        if self.collect_policy_entropy:
            try:
                if hasattr(self.model, 'get_distribution'):
                    dist = self.model.get_distribution(
                        self.training_env.get_attr('obs')[0]
                    )
                    if hasattr(dist, 'entropy'):
                        entropy = dist.entropy().mean()
                        self.logger.record("policy/entropy", entropy.cpu().numpy())
            except Exception as e:
                if self.verbose > 0:
                    logger.debug(f"Erro ao coletar entropia: {e}")
        
        return True
