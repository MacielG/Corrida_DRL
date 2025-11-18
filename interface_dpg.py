"""Interface gráfica pygame-only para Corrida DRL (sem Dear PyGui).

Simplificação radical: usa apenas Pygame para interface completa.
"""
import pygame
import numpy as np
import psutil
import time
import math
from config import ENV_SCALE
from environment import CorridaEnv
from metrics import Metrics
from logger import setup_logger
from interface_menu import InterfaceMenu
from interface_select import SelectScreen
from interface_ranking import RankingScreen
from interface_dashboard import Dashboard

logger = setup_logger()

class InterfaceDPG:
    """Interface gráfica com Pygame puro (sem Dear PyGui)."""
    def __init__(self, width=1280, height=720, fase_desc="", n_parallel=1):
        pygame.init()
        pygame.font.init()
        self.width = width
        self.height = height
        self.sim_width = int(width * 0.7)
        self.dash_width = width - self.sim_width
        self.fase_desc = fase_desc
        self.n_parallel = n_parallel
        self.grid_cols = int(math.ceil(math.sqrt(n_parallel)))
        self.grid_rows = int(math.ceil(n_parallel / self.grid_cols))
        self.cell_width = self.sim_width // self.grid_cols
        self.cell_height = height // self.grid_rows
        self.paused = False
        self.state = "menu_inicial"
        self.selected_agent = None
        self.selected_map = None
        self.ranking_data = {}
        self.metrics = [Metrics() for _ in range(n_parallel)]
        self.checkpoints = []
        self.theme = "light"
        self.fps_limit = 60
        self.resource_check_interval = 1.0
        self.last_resource_check = time.time()
        
        # Pygame surface principal
        self.pygame_screen = pygame.Surface((width, height))
        self.screen = self.pygame_screen
        self.display = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Corrida DRL")
        self.clock = pygame.time.Clock()
        
        # Componentes UI
        self.menu = InterfaceMenu(width, height)
        self.select_screen = SelectScreen(width, height)
        self.ranking_screen = RankingScreen(width, height)
        self.dashboard = Dashboard(self.screen, self.sim_width, self.dash_width, height)
        
        # Estados
        self._restart_requested = False
        self.last_car_pos = None
        
        self.adjust_resources()
        logger.info(f"Interface inicializada: {width}x{height}, {n_parallel} ambientes paralelos")

    def adjust_resources(self):
        """Ajusta FPS baseado em recursos disponíveis."""
        cpu_usage = psutil.cpu_percent(interval=0.1)
        mem_available = psutil.virtual_memory().available / (1024 ** 3)
        if self.width <= 800 or cpu_usage > 80 or mem_available < 2:
            self.fps_limit = 30
            logger.info("Modo leve: FPS=30")
        elif self.width >= 1920:
            self.fps_limit = 60
            logger.info("Modo completo: FPS=60")
        else:
            self.fps_limit = 45
            logger.info("Modo padrão: FPS=45")

    def process_events(self):
        """Processa eventos pygame."""
        if time.time() - self.last_resource_check > self.resource_check_interval:
            self.adjust_resources()
            self.last_resource_check = time.time()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.change_state("menu_inicial")

    def update(self):
        """Atualiza display."""
        self.display.blit(self.pygame_screen, (0, 0))
        pygame.display.flip()
        self.clock.tick(self.fps_limit)

    def clear(self):
        """Limpa tela."""
        self.pygame_screen.fill((255, 255, 255))

    def change_state(self, new_state):
        """Muda estado da interface."""
        self.state = new_state
        self.clear()
        logger.debug(f"Estado: {new_state}")

    def toggle_pause(self):
        """Alterna pausa."""
        self.paused = not self.paused

    def request_restart(self):
        """Solicita restart."""
        self._restart_requested = True

    def should_restart(self):
        """Verifica se restart foi solicitado."""
        return getattr(self, '_restart_requested', False)

    def clear_restart(self):
        """Limpa flag de restart."""
        self._restart_requested = False

    def close(self):
        """Fecha interface."""
        pygame.quit()

    def load_ranking_data(self, filename="ranking.json"):
        """Carrega dados de ranking."""
        from interface_ranking import load_ranking
        self.ranking_data = load_ranking(filename)

    def save_ranking_data(self, filename="ranking.json"):
        """Salva dados de ranking."""
        from interface_ranking import save_ranking
        save_ranking(self.ranking_data, filename)

    def draw_corridor(self, corridor_rect):
        """Desenha corredor."""
        pygame.draw.rect(self.pygame_screen, (0, 0, 0), corridor_rect, 8)

    def draw_barriers(self, barriers):
        """Desenha barreiras."""
        if barriers:
            for bx, by, bw, bh in barriers:
                pygame.draw.rect(self.pygame_screen, (100, 100, 100), pygame.Rect(bx, by, bw, bh))

    def draw_checkpoints(self, checkpoints, success_idx=None):
        """Desenha checkpoints."""
        t = time.time()
        for i, cp in enumerate(checkpoints):
            if success_idx is not None and i == success_idx:
                raio = int(10 * ENV_SCALE * (1 + 0.5 * math.sin(t*4)))
                cor = (0, int(255 * abs(math.sin(t*2))), 0)
            else:
                raio = int(10 * ENV_SCALE)
                cor = (0, 255, 0)
            pygame.draw.circle(self.pygame_screen, cor, (int(cp[0]), int(cp[1])), raio)

    def draw_car(self, pos, angle, color=(255, 0, 0), show=True, traj=None):
        """Desenha carro com trajetória."""
        if not show:
            return
        if not hasattr(self, 'last_car_pos') or self.last_car_pos is None:
            self.last_car_pos = [float(pos[0]), float(pos[1])]
        
        dt = self.clock.get_time() / 16.67
        interp_pos = [
            self.last_car_pos[0] + (pos[0] - self.last_car_pos[0]) * min(dt, 1.0),
            self.last_car_pos[1] + (pos[1] - self.last_car_pos[1]) * min(dt, 1.0)
        ]
        
        # Desenha trajetória
        if traj and len(traj) > 1:
            pontos = [(int(float(x)), int(float(y))) for x, y in traj if isinstance(x, (int, float)) and isinstance(y, (int, float))]
            n = len(pontos)
            for i in range(1, n):
                age = n - i
                fade = max(0, 255 - age * 10)
                cor = (255, 0, 0, fade) if fade > 0 else (255, 0, 0)
                if i < n:
                    pygame.draw.line(self.pygame_screen, cor[:3], pontos[i-1], pontos[i], 2)
        
        # Desenha carro
        car_surf = pygame.Surface((int(40*ENV_SCALE), int(20*ENV_SCALE)), pygame.SRCALPHA)
        car_surf.fill(color)
        car_rot = pygame.transform.rotate(car_surf, angle)
        rect = car_rot.get_rect(center=(int(interp_pos[0]), int(interp_pos[1])))
        self.pygame_screen.blit(car_rot, rect.topleft)
        self.last_car_pos = [float(pos[0]), float(pos[1])]

    def draw_env_grid_simple(self, env_single, idx):
        """Desenha ambiente simples em grid (NOVO - substitui draw_env_grid)."""
        col = idx % self.grid_cols
        row = idx // self.grid_cols
        offset_x = col * self.cell_width
        offset_y = row * self.cell_height
        
        # Limpa célula
        pygame.draw.rect(self.pygame_screen, (240, 240, 240), 
                        (offset_x, offset_y, self.cell_width, self.cell_height))
        pygame.draw.rect(self.pygame_screen, (100, 100, 100), 
                        (offset_x, offset_y, self.cell_width, self.cell_height), 2)
        
        # Desenha componentes do ambiente em escala reduzida
        if env_single.corridor_rect:
            cx0, cy0, cw, ch = env_single.corridor_rect
            # Escala para caber na célula
            scale_x = self.cell_width / env_single.width
            scale_y = self.cell_height / env_single.height
            rect = pygame.Rect(offset_x + cx0*scale_x, offset_y + cy0*scale_y, 
                             cw*scale_x, ch*scale_y)
            pygame.draw.rect(self.pygame_screen, (200, 200, 200), rect)
        
        # Desenha barreiras
        for bx, by, bw, bh in env_single.barriers:
            scale_x = self.cell_width / env_single.width
            scale_y = self.cell_height / env_single.height
            rect = pygame.Rect(offset_x + bx*scale_x, offset_y + by*scale_y,
                             bw*scale_x, bh*scale_y)
            pygame.draw.rect(self.pygame_screen, (100, 100, 100), rect)
        
        # Desenha checkpoints
        for cp in env_single.checkpoints:
            scale_x = self.cell_width / env_single.width
            scale_y = self.cell_height / env_single.height
            pos_x = int(offset_x + cp[0] * scale_x)
            pos_y = int(offset_y + cp[1] * scale_y)
            pygame.draw.circle(self.pygame_screen, (0, 255, 0), (pos_x, pos_y), 3)
        
        # Desenha carro
        scale_x = self.cell_width / env_single.width
        scale_y = self.cell_height / env_single.height
        car_x = int(offset_x + env_single.car1_pos[0] * scale_x)
        car_y = int(offset_y + env_single.car1_pos[1] * scale_y)
        pygame.draw.circle(self.pygame_screen, (255, 0, 0), (car_x, car_y), 4)

    def draw_car_grid(self, pos, angle, idx, color=(255, 0, 0)):
        """Desenha carro em grid (compatível com run_curriculum)."""
        col = idx % self.grid_cols
        row = idx // self.grid_cols
        offset_x = col * self.cell_width
        offset_y = row * self.cell_height
        
        car_surf = pygame.Surface((int(40*ENV_SCALE), int(20*ENV_SCALE)), pygame.SRCALPHA)
        car_surf.fill(color)
        car_rot = pygame.transform.rotate(car_surf, angle)
        rect = car_rot.get_rect(center=(int(pos[0])+offset_x, int(pos[1])+offset_y))
        self.pygame_screen.blit(car_rot, rect.topleft)

    def draw_dashboard(self, rewards_hist, collisions_hist, penalties_hist, ciclo, avg_speed, n_dif):
        """Desenha dashboard."""
        self.dashboard.draw_dashboard(
            rewards_hist, collisions_hist, penalties_hist, ciclo, avg_speed, n_dif,
            self.fase_desc, self.n_parallel, self.checkpoints
        )

    def draw_loading(self, text, progresso=0.5, animar=True):
        """Desenha tela de loading."""
        self.clear()
        font = pygame.font.Font(None, 32)
        text_surf = font.render(text, True, (50, 50, 50))
        text_rect = text_surf.get_rect(center=(self.width//2, self.height//2 - 50))
        self.pygame_screen.blit(text_surf, text_rect)
        
        # Barra de progresso
        bar_width = 300
        bar_height = 30
        bar_x = self.width//2 - bar_width//2
        bar_y = self.height//2
        pygame.draw.rect(self.pygame_screen, (200, 200, 200), 
                        (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(self.pygame_screen, (0, 200, 0), 
                        (bar_x, bar_y, bar_width * progresso, bar_height))
        pygame.draw.rect(self.pygame_screen, (0, 0, 0), 
                        (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Percentual
        percent_text = font.render(f"{int(progresso*100)}%", True, (50, 50, 50))
        percent_rect = percent_text.get_rect(center=(self.width//2, bar_y + bar_height + 20))
        self.pygame_screen.blit(percent_text, percent_rect)
        
        self.update()
