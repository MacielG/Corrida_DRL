"""Métricas e utilitários para avaliação de desempenho no Corrida DRL.

Fornece classes e funções para registrar recompensas, colisões, checkpoints e gerar estatísticas do agente.
"""
import pygame
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend to avoid tkinter issues
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
import gc
import time
import pandas as pd

class Metrics:
    """Classe utilitária para registrar e calcular métricas de desempenho do agente.

    Attributes:
        rewards (list): Histórico de recompensas.
        collisions (list): Histórico de colisões.
        checkpoints (list): Histórico de checkpoints atingidos.
    """
    def __init__(self):
        self.rewards = []
        self.collisions = []
        self.episode_times = []
        self.checkpoints = []
        self.fig, self.ax = plt.subplots(figsize=(3, 2))
        self.update_counter = 0

    def update(self, reward, collisions, episode_time=None, checkpoint=None):
        self.rewards.append(reward)
        self.collisions.append(collisions)
        if episode_time is not None:
            self.episode_times.append(episode_time)
        if checkpoint is not None:
            self.checkpoints.append(checkpoint)
        if len(self.rewards) > 100:
            self.rewards.pop(0)
            self.collisions.pop(0)
            if self.episode_times:
                self.episode_times.pop(0)
            if self.checkpoints:
                self.checkpoints.pop(0)
        self.update_counter += 1
        # Limpa listas a cada 1000 updates para evitar uso excessivo de memória
        if self.update_counter % 1000 == 0:
            self.rewards = self.rewards[-100:]
            self.collisions = self.collisions[-100:]
            self.episode_times = self.episode_times[-100:]
            self.checkpoints = self.checkpoints[-100:]
            gc.collect()

    def compute_moving_average(self, data, window=10):
        """Calcula a média móvel de uma lista de dados.
        Args:
            data (list): Lista de valores.
            window (int): Tamanho da janela.
        Returns:
            np.ndarray: Série da média móvel.
        """
        if len(data) < window:
            return np.array([])
        return np.convolve(data, np.ones(window)/window, mode='valid')

    def render(self, screen, render_interval=10):
        # Só atualiza o gráfico a cada N frames
        if self.update_counter % render_interval != 0:
            return
        self.ax.clear()
        # Gráficos de média móvel
        if len(self.rewards) >= 10:
            self.ax.plot(self.compute_moving_average(self.rewards), label="Recompensa (média)")
        if len(self.collisions) >= 10:
            self.ax.plot(self.compute_moving_average(self.collisions), label="Colisões (média)")
        if self.checkpoints and len(self.checkpoints) >= 10:
            self.ax.plot(self.compute_moving_average(self.checkpoints), label="Checkpoint (média)")
        self.ax.legend()
        self.ax.set_title("Performance")
        canvas = FigureCanvasAgg(self.fig)
        canvas.draw()
        renderer = canvas.get_renderer()
        # Use buffer_rgba() instead of deprecated tostring_rgb()
        raw_data = renderer.buffer_rgba()
        size = canvas.get_width_height()
        # Convert RGBA to RGB by converting to string then using RGB
        import numpy as np
        data_array = np.frombuffer(raw_data, dtype=np.uint8).reshape((*size[::-1], 4))
        # Drop alpha channel, keep only RGB
        rgb_array = data_array[:, :, :3]
        # Create surface from RGB array
        surf = pygame.surfarray.make_surface(np.transpose(rgb_array, (1, 0, 2)))
        screen.blit(surf, (550, 10))

    def export_metrics(self, filename="metrics.csv"):
        """Exporta métricas para um arquivo CSV usando pandas."""
        df = pd.DataFrame({
            "rewards": self.rewards,
            "collisions": self.collisions,
            "episode_times": self.episode_times,
            "checkpoints": self.checkpoints
        })
        df.to_csv(filename, index=False)
