"""
Interface gráfica para Corrida DRL, exibe escala, tempo e fase.
"""
import pygame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from config import ENV_SCALE, TIME_STEP
import math
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from logger import setup_logger
import time

logger = setup_logger()

class Interface:
    """Interface gráfica principal para visualização do ambiente Corrida DRL.

    Args:
        width (int): Largura da janela.
        height (int): Altura da janela.
        fase_desc (str): Descrição da fase.
        n_parallel (int): Número de execuções paralelas.
    """
    def __init__(self, width=1200, height=600, fase_desc="", n_parallel=1):
        pygame.init()
        # Área de simulação ocupa 70%, dashboard 30%
        self.sim_width = int(width * 0.7)
        self.dash_width = width - self.sim_width
        self.width = width
        self.height = height
        self.n_parallel = n_parallel
        self.grid_cols = int(math.ceil(math.sqrt(n_parallel)))
        self.grid_rows = int(math.ceil(n_parallel / self.grid_cols))
        self.cell_width = self.sim_width // self.grid_cols
        self.cell_height = height // self.grid_rows
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.fase_desc = fase_desc
        self.rewards = []
        self.collisions = []
        self.penalties = []
        self.episode_times = []
        self.checkpoints = []
        self.update_counter = 0
        # Dashboard pygame
        self.dashboard_rect = pygame.Rect(self.sim_width, 0, self.dash_width, self.height)
        self.paused = False
        self.buttons = self._create_buttons()
        self.selected_map = None
        self.menu_active = False
        self.menu_options = ["corridor", "curve"]
        self.menu_rects = []

    def _create_buttons(self):
        btns = {}
        btns["pause"] = pygame.Rect(self.sim_width+20, 30, 120, 40)
        btns["restart"] = pygame.Rect(self.sim_width+20, 80, 120, 40)
        btns["map"] = pygame.Rect(self.sim_width+20, 130, 120, 40)
        return btns

    def process_events(self):
        """Processa eventos do pygame (teclado, fechar janela)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if self.menu_active:
                    for i, rect in enumerate(self.menu_rects):
                        if rect.collidepoint(mx, my):
                            self.selected_map = self.menu_options[i]
                            self.menu_active = False
                            break  # Sai do loop após selecionar
                else:
                    if self.buttons["pause"].collidepoint(mx, my):
                        self.paused = not self.paused
                    elif self.buttons["restart"].collidepoint(mx, my):
                        self._restart_requested = True
                    elif self.buttons["map"].collidepoint(mx, my):
                        self.menu_active = True
                        # Populate menu_rects immediately when menu is activated
                        self.menu_rects = []
                        menu_x, menu_y = self.sim_width + 20, self.buttons["map"].y + 50
                        for i, opt in enumerate(self.menu_options):
                            rect = pygame.Rect(menu_x, menu_y + i * 50, 120, 40)
                            self.menu_rects.append(rect)

    def draw_corridor(self, corridor_rect):
        """Desenha o corredor principal na tela.

        Args:
            corridor_rect (tuple): Retângulo do corredor.
        """
        pygame.draw.rect(self.screen, (0, 0, 0), corridor_rect, 8)

    def draw_barriers(self, barriers):
        """Desenha as barreiras do mapa usando operação vetorial."""
        if barriers:
            for bx, by, bw, bh in barriers:
                pygame.draw.rect(self.screen, (100, 100, 100), pygame.Rect(bx, by, bw, bh))

    def draw_checkpoints(self, checkpoints, success_idx=None):
        """Desenha os checkpoints do mapa de forma otimizada, com efeito de brilho no atingido."""
        t = time.time()
        for i, cp in enumerate(checkpoints):
            if success_idx is not None and i == success_idx:
                # Efeito de brilho pulsante
                raio = int(10 * ENV_SCALE * (1 + 0.5 * math.sin(t*4)))
                cor = (0, int(255 * abs(math.sin(t*2))), 0)
            else:
                raio = int(10 * ENV_SCALE)
                cor = (0, 255, 0)
            pygame.draw.circle(self.screen, cor, (int(cp[0]), int(cp[1])), raio)

    def draw_car(self, pos, angle, color=(255,0,0,128), show=True, traj=None):
        """Desenha o carro e sua trajetória com animação suave e fade na trilha.

        Args:
            pos (list): Posição do carro.
            angle (float): Ângulo do carro.
            color (tuple): Cor RGBA.
            show (bool): Se True, exibe o carro.
            traj (list): Trajetória do carro.
        """
        if not show:
            return
        # Animação suave da posição
        if not hasattr(self, 'last_car_pos') or self.last_car_pos is None:
            self.last_car_pos = [float(pos[0]), float(pos[1])]
        dt = self.clock.get_time() / 16.67  # 60 FPS base
        interp_pos = [
            self.last_car_pos[0] + (pos[0] - self.last_car_pos[0]) * min(dt, 1.0),
            self.last_car_pos[1] + (pos[1] - self.last_car_pos[1]) * min(dt, 1.0)
        ]
        # Desenha a trajetória com fade
        if traj and len(traj) > 1:
            pontos = [(int(float(x)), int(float(y))) for x, y in traj if isinstance(x, (int, float)) and isinstance(y, (int, float))]
            n = len(pontos)
            for i in range(1, n):
                age = n - i
                fade = max(0, 255 - age * 10)
                cor = (255, 0, 0, fade)
                s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                pygame.draw.line(s, cor, pontos[i-1], pontos[i], 2)
                self.screen.blit(s, (0,0))
        car_surf = pygame.Surface((int(40*ENV_SCALE), int(20*ENV_SCALE)), pygame.SRCALPHA)
        car_surf.fill(color)
        car_rot = pygame.transform.rotate(car_surf, angle)
        rect = car_rot.get_rect(center=(int(interp_pos[0]), int(interp_pos[1])))
        self.screen.blit(car_rot, rect.topleft)
        self.last_car_pos = [float(pos[0]), float(pos[1])]

    def draw_car_grid(self, pos, angle, idx, color=(255,0,0)):
        """Desenha o carro em um grid de execuções paralelas.

        Args:
            pos (list): Posição do carro.
            angle (float): Ângulo do carro.
            idx (int): Índice do grid.
            color (tuple): Cor RGB.
        """
        col = idx % self.grid_cols
        row = idx // self.grid_rows
        offset_x = col * self.cell_width
        offset_y = row * self.cell_height
        car_surf = pygame.Surface((int(40*ENV_SCALE), int(20*ENV_SCALE)), pygame.SRCALPHA)
        car_surf.fill(color)
        car_rot = pygame.transform.rotate(car_surf, angle)
        rect = car_rot.get_rect(center=(int(pos[0])+offset_x, int(pos[1])+offset_y))
        self.screen.blit(car_rot, rect.topleft)

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
        self.screen.blit(surf, (self.width-250, 10))

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

    def draw_map(self, env):
        """Desenha o mapa completo (corredor, barreiras, checkpoints).

        Args:
            env (CorridaEnv): Ambiente de corrida.
        """
        if env.map_type == "corridor" and env.corridor_rect:
            self.draw_corridor(env.corridor_rect)
            self.draw_barriers(env.barriers)
            self.draw_checkpoints(env.checkpoints)
        elif env.map_type == "curve":
            self.draw_barriers(env.barriers)
            self.draw_checkpoints(env.checkpoints)

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
        dash = self.dashboard_rect
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
        # Taxa de sucesso
        if self.checkpoints:
            success_count = sum(1 for c in self.checkpoints if c > 0)
            total = len(self.checkpoints)
            success_rate = (success_count / total * 100) if total > 0 else 0.0
            self.screen.blit(font.render(f"Taxa de sucesso: {success_rate:.1f}%", True, (0,128,0)), (self.sim_width+20, y))
            y += 30
        # Menu de mapas
        if self.menu_active:
            self.menu_rects = []
            menu_x, menu_y = self.sim_width+20, y+20
            for i, opt in enumerate(self.menu_options):
                rect = pygame.Rect(menu_x, menu_y+i*50, 120, 40)
                pygame.draw.rect(self.screen, (180,220,255), rect)
                self.screen.blit(font.render(opt, True, (0,0,0)), (rect.x+10, rect.y+10))
                self.menu_rects.append(rect)

    def draw_dashboard(self, rewards_hist, collisions_hist, penalties_hist, ciclo, avg_speed, n_dif):
        """Atualiza o dashboard com métricas do episódio.

        Args:
            rewards_hist (list): Histórico de recompensas.
            collisions_hist (list): Histórico de colisões.
            penalties_hist (list): Histórico de penalizações.
            ciclo (int): Ciclo atual.
            avg_speed (float): Velocidade média.
            n_dif (int): Número de estados diferentes.
        """
        self.draw_dashboard_pygame(rewards_hist, collisions_hist, penalties_hist, ciclo, avg_speed, n_dif)

    def should_restart(self):
        return getattr(self, '_restart_requested', False)
    def clear_restart(self):
        self._restart_requested = False

    def update(self):
        """Atualiza a tela do pygame."""
        pygame.display.flip()
        self.clock.tick(60)

    def clear(self):
        """Limpa a tela para o próximo frame."""
        # Limpa área de simulação e dashboard separadamente
        self.screen.fill((255, 255, 255))
        pygame.draw.rect(self.screen, (255,255,255), (0, 0, self.sim_width, self.height))
        pygame.draw.rect(self.screen, (245,245,245), (self.sim_width, 0, self.dash_width, self.height))

    def close(self):
        """Fecha a interface e libera recursos."""
        pygame.quit()
        # Garante liberação de recursos
        import gc
        gc.collect()

    def draw_env_grid(self, env, idx, car_color=(255,0,0)):
        """Desenha o ambiente em um grid para execuções paralelas.

        Args:
            env (CorridaEnv): Ambiente de corrida.
            idx (int): Índice do grid.
            car_color (tuple): Cor do carro.
        """
        col = idx % self.grid_cols
        row = idx // self.grid_rows
        offset_x = col * self.cell_width
        offset_y = row * self.cell_height
        # Desenha apenas na área de simulação
        grid_surf = pygame.Surface((self.cell_width, self.cell_height))
        grid_surf.fill((255,255,255))
        # Desenha mapa, barreiras, checkpoints
        if env.map_type == "corridor" and env.corridor_rect:
            # Corrige coordenadas para o grid
            rect = (
                int(env.corridor_rect[0] * self.cell_width / env.width),
                int(env.corridor_rect[1] * self.cell_height / env.height),
                int(env.corridor_rect[2] * self.cell_width / env.width),
                int(env.corridor_rect[3] * self.cell_height / env.height)
            )
            pygame.draw.rect(grid_surf, (0,0,0), rect, 8)
            for barrier in env.barriers:
                bx, by, bw, bh = barrier
                bx = int(bx * self.cell_width / env.width)
                by = int(by * self.cell_height / env.height)
                bw = int(bw * self.cell_width / env.width)
                bh = int(bh * self.cell_height / env.height)
                pygame.draw.rect(grid_surf, (100,100,100), (bx,by,bw,bh))
            for cp in env.checkpoints:
                cx = int(cp[0] * self.cell_width / env.width)
                cy = int(cp[1] * self.cell_height / env.height)
                pygame.draw.circle(grid_surf, (0,255,0), (cx,cy), int(10*ENV_SCALE*self.cell_width/env.width))
        elif env.map_type == "curve":
            for barrier in env.barriers:
                bx, by, bw, bh = barrier
                bx = int(bx * self.cell_width / env.width)
                by = int(by * self.cell_height / env.height)
                bw = int(bw * self.cell_width / env.width)
                bh = int(bh * self.cell_height / env.height)
                pygame.draw.rect(grid_surf, (100,100,100), (bx,by,bw,bh))
            for cp in env.checkpoints:
                cx = int(cp[0] * self.cell_width / env.width)
                cy = int(cp[1] * self.cell_height / env.height)
                pygame.draw.circle(grid_surf, (0,255,0), (cx,cy), int(10*ENV_SCALE*self.cell_width/env.width))
        # Desenha o carro
        car_x = int(env.car1_pos[0] * self.cell_width / env.width)
        car_y = int(env.car1_pos[1] * self.cell_height / env.height)
        car_surf = pygame.Surface((int(40*ENV_SCALE*self.cell_width/env.width), int(20*ENV_SCALE*self.cell_height/env.height)), pygame.SRCALPHA)
        car_surf.fill(car_color)
        car_rot = pygame.transform.rotate(car_surf, env.car1_angle)
        rect = car_rot.get_rect(center=(car_x, car_y))
        grid_surf.blit(car_rot, rect.topleft)
        # Blit do grid para a tela principal
        self.screen.blit(grid_surf, (offset_x, offset_y))

    def draw_multi_agents(self, env, states=None, trajs=None):
        """Desenha múltiplos agentes de um VecEnv na interface.

        Args:
            env (VecEnv): Instância do DummyVecEnv/SubprocVecEnv.
            states (list): Lista de estados normalizados (opcional).
            trajs (list): Lista de trajetórias (opcional).
        """
        if states is None:
            states = env.reset()  # fallback, mas normalmente deve ser passado
        n = len(states)
        for idx, state in enumerate(states):
            alpha = int(80 + 175 * (1 - idx/(n-1))) if n > 1 else 255
            traj = trajs[idx] if trajs is not None and idx < len(trajs) else None
            self.draw_car(state[0:2], state[3], color=(255,0,0,alpha), show=True, traj=traj)
