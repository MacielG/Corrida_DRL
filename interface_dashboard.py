import pygame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

class Dashboard:
    def __init__(self, screen, sim_width, dash_width, height):
        self.screen = screen
        self.sim_width = sim_width
        self.dash_width = dash_width
        self.height = height
        self.fig, self.ax = plt.subplots(figsize=(3, 2))
        self.update_counter = 0

    def draw_dashboard(self, rewards_hist, collisions_hist, penalties_hist, ciclo, avg_speed, n_dif, fase_desc, n_parallel, checkpoints):
        dash = pygame.Rect(self.sim_width, 0, self.dash_width, self.height)
        pygame.draw.rect(self.screen, (245,245,245), dash)
        font = pygame.font.SysFont(None, 24)
        # Gráfico matplotlib no topo do dashboard
        graph_y = 10
        if rewards_hist and len(rewards_hist[0]) > 0:
            n = len(rewards_hist)
            maxlen = min(100, max(len(r) for r in rewards_hist))
            avg_rewards = [sum([r[i] if i < len(r) else 0 for r in rewards_hist])/n for i in range(maxlen)]
            avg_collisions = [sum([c[i] if i < len(c) else 0 for c in collisions_hist])/n for i in range(maxlen)]
            fig, ax = plt.subplots(figsize=(2.8, 2.0), dpi=100)
            ax.plot(avg_rewards, label="Recompensa média", color='tab:blue')
            ax.plot(avg_collisions, label="Colisões médias", color='tab:red')
            if penalties_hist:
                avg_penalties = [sum([p[i] if i < len(p) else 0 for p in penalties_hist])/n for i in range(maxlen)]
                ax.plot(avg_penalties, label="Penalização média", color='tab:orange')
            ax.legend(fontsize=8, loc='upper right')
            ax.set_title("Desempenho Geral", fontsize=10)
            ax.set_xlabel("Ciclos")
            ax.set_ylabel("Valor")
            ax.grid(True, linestyle='--', alpha=0.3)
            fig.tight_layout()
            canvas = FigureCanvasAgg(fig)
            canvas.draw()
            renderer = canvas.get_renderer()
            # Use buffer_rgba() instead of deprecated tostring_rgb()
            raw_data = renderer.buffer_rgba()
            size = canvas.get_width_height()
            import numpy as np
            data_array = np.frombuffer(raw_data, dtype=np.uint8).reshape((*size[::-1], 4))
            rgb_array = data_array[:, :, :3]
            surf = pygame.surfarray.make_surface(np.transpose(rgb_array, (1, 0, 2)))
            self.screen.blit(surf, (self.sim_width+10, graph_y))
            plt.close(fig)
        # Info
        y = graph_y + 220
        lines = [
            f"Ciclos: {ciclo}",
            f"Média velocidade: {avg_speed:.2f}",
            f"Execuções paralelas: {n_parallel}",
            f"Diferentes: {n_dif}",
            f"Fase: {fase_desc}"
        ]
        for line in lines:
            self.screen.blit(font.render(line, True, (0,0,0)), (self.sim_width+20, y))
            y += 30
        # Taxa de sucesso
        if checkpoints:
            success_count = sum(1 for c in checkpoints if c > 0)
            total = len(checkpoints)
            success_rate = (success_count / total * 100) if total > 0 else 0.0
            self.screen.blit(font.render(f"Taxa de sucesso: {success_rate:.1f}%", True, (0,128,0)), (self.sim_width+20, y))
            y += 30

    def draw_metrics(self, rewards, collisions):
        """Desenha gráfico de recompensas e colisões.

        Args:
            rewards (list): Histórico de recompensas.
            collisions (list): Histórico de colisões.
        """
        self.ax.clear()
        self.ax.plot(rewards, label="Recompensa")
        self.ax.plot(collisions, label="Colisões")
        self.ax.legend()
        self.ax.set_title("Performance")
        canvas = FigureCanvasAgg(self.fig)
        canvas.draw()
        renderer = canvas.get_renderer()
        raw_data = renderer.tostring_rgb()
        size = canvas.get_width_height()
        surf = pygame.image.fromstring(raw_data, size, "RGB")
        self.screen.blit(surf, (self.sim_width-250, 10))

    def draw_metrics_grid(self, rewards_hist, collisions_hist, penalties_hist=None):
        """Desenha gráficos médios de desempenho para execuções paralelas.

        Args:
            rewards_hist (list): Histórico de recompensas.
            collisions_hist (list): Histórico de colisões.
            penalties_hist (list): Histórico de penalizações.
        """
        n = len(rewards_hist)
        if n == 0:
            return
        avg_rewards = [sum([r[i] if i < len(r) else 0 for r in rewards_hist])/n for i in range(max(len(r) for r in rewards_hist))]
        avg_collisions = [sum([c[i] if i < len(c) else 0 for c in collisions_hist])/n for i in range(max(len(c) for c in collisions_hist))]
        self.ax.clear()
        self.ax.plot(avg_rewards, label="Recompensa média", color='tab:blue')
        self.ax.plot(avg_collisions, label="Colisões médias", color='tab:red')
        if penalties_hist:
            avg_penalties = [sum([p[i] if i < len(p) else 0 for p in penalties_hist])/n for i in range(max(len(p) for p in penalties_hist))]
            self.ax.plot(avg_penalties, label="Penalização média", color='tab:orange')
        self.ax.legend(fontsize=8, loc='upper right')
        self.ax.set_title("Desempenho Geral", fontsize=10)
        self.ax.set_xlabel("Ciclos")
        self.ax.set_ylabel("Valor")
        self.fig.set_size_inches(3, 2)
        self.ax.grid(True, linestyle='--', alpha=0.3)
        canvas = FigureCanvasAgg(self.fig)
        canvas.draw()
        renderer = canvas.get_renderer()
        raw_data = renderer.tostring_rgb()
        size = canvas.get_width_height()
        surf = pygame.image.fromstring(raw_data, size, "RGB")
        # Blit do gráfico na área do dashboard à direita
        self.screen.blit(surf, (self.sim_width+10, 30))

    def draw_info(self, ciclo, avg_speed=0.0, n_dif=0):
        """Exibe informações textuais do episódio.

        Args:
            ciclo (int): Ciclo atual.
            avg_speed (float): Velocidade média.
            n_dif (int): Número de estados diferentes.
        """
        font = pygame.font.SysFont(None, 24)
        info = f"Ciclos: {ciclo}"
        info2 = f"Média velocidade: {avg_speed:.2f}"
        info3 = f"Execuções paralelas: {self.n_parallel}"
        info4 = f"Diferentes: {n_dif}"
        info5 = f"Fase: {self.fase_desc}"
        self.screen.blit(font.render(info, True, (0,0,0)), (self.sim_width+10, 10))
        self.screen.blit(font.render(info2, True, (0,0,0)), (self.sim_width+10, 60))
        self.screen.blit(font.render(info3, True, (0,0,0)), (self.sim_width+10, 90))
        self.screen.blit(font.render(info4, True, (0,0,0)), (self.sim_width+10, 120))
        self.screen.blit(font.render(info5, True, (0,0,0)), (self.sim_width+10, 150))

    def draw_dashboard_pygame(self, rewards_hist, collisions_hist, penalties_hist, ciclo, avg_speed, n_dif):
        dash = pygame.Rect(self.sim_width, 0, self.dash_width, self.height)
        pygame.draw.rect(self.screen, (245,245,245), dash)
        font = pygame.font.SysFont(None, 24)
        # Gráfico matplotlib no topo do dashboard
        graph_y = 10
        if rewards_hist and len(rewards_hist[0]) > 0:
            n = len(rewards_hist)
            maxlen = min(100, max(len(r) for r in rewards_hist))
            avg_rewards = [sum([r[i] if i < len(r) else 0 for r in rewards_hist])/n for i in range(maxlen)]
            avg_collisions = [sum([c[i] if i < len(c) else 0 for c in collisions_hist])/n for i in range(maxlen)]
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_agg import FigureCanvasAgg
            fig, ax = plt.subplots(figsize=(2.8, 2.0), dpi=100)
            ax.plot(avg_rewards, label="Recompensa média", color='tab:blue')
            ax.plot(avg_collisions, label="Colisões médias", color='tab:red')
            if penalties_hist:
                avg_penalties = [sum([p[i] if i < len(p) else 0 for p in penalties_hist])/n for i in range(maxlen)]
                ax.plot(avg_penalties, label="Penalização média", color='tab:orange')
            ax.legend(fontsize=8, loc='upper right')
            ax.set_title("Desempenho Geral", fontsize=10)
            ax.set_xlabel("Ciclos")
            ax.set_ylabel("Valor")
            ax.grid(True, linestyle='--', alpha=0.3)
            fig.tight_layout()
            canvas = FigureCanvasAgg(fig)
            canvas.draw()
            renderer = canvas.get_renderer()
            raw_data = renderer.tostring_rgb()
            size = canvas.get_width_height()
            surf = pygame.image.fromstring(raw_data, size, "RGB")
            self.screen.blit(surf, (self.sim_width+10, graph_y))
            plt.close(fig)
        # Botões logo abaixo do gráfico
        btn_y_start = graph_y + 210
        btn_gap = 15
        btn_height = 40
        btn_width = 120
        btn_x = self.sim_width+20
        self.buttons["pause"].y = btn_y_start
        self.buttons["restart"].y = btn_y_start + btn_height + btn_gap
        self.buttons["map"].y = btn_y_start + 2*(btn_height + btn_gap)
        for key in self.buttons:
            self.buttons[key].x = btn_x
        for key in self.buttons:
            pygame.draw.rect(self.screen, (200,200,200), self.buttons[key])
        # Texto dinâmico do botão Pausar/Continuar
        pause_text = "Continuar" if self.paused else "Pausar"
        self.screen.blit(font.render(pause_text, True, (0,0,0)), (self.buttons["pause"].x+10, self.buttons["pause"].y+10))
        self.screen.blit(font.render("Reiniciar", True, (0,0,0)), (self.buttons["restart"].x+10, self.buttons["restart"].y+10))
        self.screen.blit(font.render("Mudar Mapa", True, (0,0,0)), (self.buttons["map"].x+10, self.buttons["map"].y+10))
        # Info
        y = btn_y_start + 3*(btn_height + btn_gap) + 20
        lines = [
            f"Ciclos: {ciclo}",
            f"Média velocidade: {avg_speed:.2f}",
            f"Execuções paralelas: {self.n_parallel}",
            f"Diferentes: {n_dif}",
            f"Fase: {self.fase_desc}"
        ]
        for line in lines:
            self.screen.blit(font.render(line, True, (0,0,0)), (self.sim_width+20, y))
            y += 30
