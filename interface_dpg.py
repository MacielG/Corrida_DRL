import dearpygui.dearpygui as dpg
import pygame
import numpy as np
import psutil
import time
import math
from config import ENV_SCALE
from environment import CorridaEnv
from metrics import Metrics
from logger import setup_logger
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from interface_menu import InterfaceMenu
from interface_select import SelectScreen
from interface_ranking import RankingScreen
from interface_dashboard import Dashboard

logger = setup_logger()

class InterfaceDPG:
    """Interface gráfica moderna para Corrida DRL usando Dear PyGui."""
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
        self.animations_enabled = True
        self.resource_check_interval = 1.0
        self.last_resource_check = time.time()
        # Compatibilidade pygame
        self.pygame_screen = pygame.Surface((width, height))
        self.screen = self.pygame_screen
        self.clock = pygame.time.Clock()
        # Menus e telas
        self.menu = InterfaceMenu(self.width, self.height)
        self.select_screen = SelectScreen(self.width, self.height)
        self.ranking_screen = RankingScreen(self.width, self.height)
        self.dashboard = Dashboard(self.screen, self.sim_width, self.dash_width, self.height)
        # Estados e menus
        self.menu_active = False
        self.menu_rects = []
        self.menu_options = ["corridor", "curve"]
        self._restart_requested = False
        # Dear PyGui
        dpg.create_context()
        dpg.create_viewport(title="Corrida DRL", width=width, height=height, resizable=True)
        self.setup_themes()
        self.adjust_resources()
        self.setup_ui()
        self.setup_animations()
        # Garante que a tela inicial seja exibida ao iniciar
        self.change_state("menu_inicial")
        dpg.setup_dearpygui()
        dpg.show_viewport()
        # Removido dpg.start_dearpygui() para não bloquear o loop principal

    def setup_themes(self):
        # Tema claro com gradiente, bordas arredondadas e sombra
        with dpg.theme() as self.light_theme:
            with dpg.theme_component(dpg.mvAll):
                # Gradiente de fundo simulando com cor intermediária
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (240, 244, 248, 255))  # #F0F4F8
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (255, 255, 255, 230))  # Transparente
                dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (255, 255, 255, 245))
                dpg.add_theme_color(dpg.mvThemeCol_Border, (200, 220, 240, 120))
                dpg.add_theme_color(dpg.mvThemeCol_Button, (74, 144, 226, 255))  # #4A90E2
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (80, 180, 255, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (80, 200, 255, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (45, 55, 72, 255))  # #2D3748
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (255, 255, 255, 220))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (230, 245, 255, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (210, 235, 255, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (240, 244, 248, 180))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (200, 220, 240, 180))
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 12)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 12)
                dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 12)
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 8)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 12, 10)
                dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 2)
        # Tema escuro com gradiente e azul claro
        with dpg.theme() as self.dark_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (26, 32, 44, 255))  # #1A202C
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (45, 55, 72, 230))  # #2D3748
                dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (45, 55, 72, 245))
                dpg.add_theme_color(dpg.mvThemeCol_Border, (80, 120, 180, 120))
                dpg.add_theme_color(dpg.mvThemeCol_Button, (99, 179, 237, 255))  # #63B3ED
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (120, 200, 255, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (104, 211, 145, 255))  # #68D391
                dpg.add_theme_color(dpg.mvThemeCol_Text, (226, 232, 240, 255))  # #E2E8F0
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (45, 55, 72, 220))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (60, 80, 120, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (80, 120, 180, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (26, 32, 44, 180))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (99, 179, 237, 180))
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 12)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 12)
                dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 12)
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 8)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 12, 10)
                dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 2)
        dpg.bind_theme(self.light_theme)

    def adjust_resources(self):
        cpu_usage = psutil.cpu_percent(interval=0.1)
        mem_available = psutil.virtual_memory().available / (1024 ** 3)
        if self.width <= 800 or cpu_usage > 80 or mem_available < 2:
            self.fps_limit = 30
            self.animations_enabled = False
            logger.info("Modo leve: FPS=30, animações desativadas")
        elif self.width >= 1920:
            self.fps_limit = 60
            self.animations_enabled = True
            logger.info("Modo completo: FPS=60, animações habilitadas")
        else:
            self.fps_limit = 45
            self.animations_enabled = True
            logger.info("Modo padrão: FPS=45, animações habilitadas")

    def setup_ui(self):
        with dpg.window(tag="main_window", no_title_bar=True, no_resize=True, no_move=True, width=self.width, height=self.height):
            with dpg.group(horizontal=True):
                with dpg.child_window(tag="sim_area", width=self.sim_width, height=self.height):
                    dpg.add_drawlist(tag="sim_drawlist", width=self.sim_width, height=self.height)
                with dpg.child_window(tag="dash_area", width=self.dash_width, height=self.height):
                    dpg.add_text("Dashboard", tag="dash_title")
                    dpg.add_plot(tag="metrics_plot", width=self.dash_width-20, height=200)
                    dpg.add_button(label="Pausar", tag="pause_btn", callback=self.toggle_pause)
                    dpg.add_button(label="Reiniciar", tag="restart_btn", callback=self.request_restart)
                    dpg.add_button(label="Mudar Mapa", tag="map_btn", callback=self.show_map_menu)
                    dpg.add_combo(label="Tema", items=["light", "dark"], default_value="light", callback=self.change_theme)
        with dpg.window(tag="menu_window", no_title_bar=True, no_close=True, width=400, height=500, pos=[(self.width-400)//2, (self.height-500)//2], show=False):
            dpg.add_text("Corrida DRL", tag="menu_title")
            dpg.add_button(label="Treinar Agente", callback=lambda: self.change_state("selecao_agente"))
            dpg.add_button(label="Assistir Corrida", callback=lambda: self.change_state("selecao_agente"))
            dpg.add_button(label="Ranking", callback=lambda: self.change_state("ranking"))
            dpg.add_button(label="Gestão de Agentes", callback=lambda: self.change_state("gestao_agentes"))
            dpg.add_button(label="Sair", callback=self.close)
        self.setup_animations()

    def setup_animations(self):
        if self.animations_enabled:
            with dpg.item_handler_registry(tag="menu_handler"):
                dpg.add_item_visible_handler(callback=lambda: dpg.animate_item("menu_window", "scale", [0.9, 0.9], [1.0, 1.0], 300))
                dpg.add_item_visible_handler(callback=lambda: dpg.animate_item("menu_window", "alpha", 0, 255, 300))
            dpg.bind_item_handler_registry("menu_window", "menu_handler")

    def change_theme(self, sender, app_data):
        self.theme = app_data
        dpg.bind_theme(self.light_theme if app_data == "light" else self.dark_theme)
        logger.info(f"Tema alterado para: {app_data}")

    def toggle_pause(self):
        self.paused = not self.paused
        dpg.configure_item("pause_btn", label="Continuar" if self.paused else "Pausar")

    def request_restart(self):
        self._restart_requested = True

    def should_restart(self):
        return getattr(self, '_restart_requested', False)

    def clear_restart(self):
        self._restart_requested = False

    def show_map_menu(self):
        dpg.show_item("map_menu")

    def change_state(self, new_state):
        self.state = new_state
        # Esconde todas as janelas
        for tag in ["menu_window", "main_window", "gestao_window", "selecao_agente_window", "selecao_mapa_window", "ranking_window"]:
            if dpg.does_item_exist(tag):
                dpg.configure_item(tag, show=False)
        # Mostra apenas a janela do estado atual
        if new_state == "menu_inicial":
            dpg.configure_item("menu_window", show=True)
        elif new_state == "simulacao":
            dpg.configure_item("main_window", show=True)
        elif new_state == "gestao_agentes":
            if not dpg.does_item_exist("gestao_window"):
                with dpg.window(tag="gestao_window", width=500, height=600, pos=[self.width//2-250, self.height//2-300]):
                    dpg.add_text("Gestão de Agentes", tag="gestao_title")
                    self.add_voltar_button("gestao_window", lambda: self.change_state("menu_inicial"))
            dpg.configure_item("gestao_window", show=True)
            # Exibe lista de agentes
            from interface_agents import load_agents
            agents = load_agents()
            self.render_agent_list("gestao_window", agents)
        elif new_state == "selecao_agente":
            if not dpg.does_item_exist("selecao_agente_window"):
                with dpg.window(tag="selecao_agente_window", width=400, height=500, pos=[self.width//2-200, self.height//2-250]):
                    dpg.add_text("Seleção de Agente", tag="selecao_agente_title")
                    self.add_voltar_button("selecao_agente_window", lambda: self.change_state("menu_inicial"))
            dpg.configure_item("selecao_agente_window", show=True)
            # Exibe lista de agentes para seleção
            from interface_agents import load_agents
            agents = load_agents()
            self.render_agent_list("selecao_agente_window", agents)
        elif new_state == "selecao_mapa":
            if not dpg.does_item_exist("selecao_mapa_window"):
                with dpg.window(tag="selecao_mapa_window", width=400, height=400, pos=[self.width//2-200, self.height//2-200]):
                    dpg.add_text("Seleção de Mapa", tag="selecao_mapa_title")
                    self.add_voltar_button("selecao_mapa_window", lambda: self.change_state("selecao_agente"))
            dpg.configure_item("selecao_mapa_window", show=True)
            # Exibe lista de mapas
            maps = ["corridor", "curve", "circle"]
            self.render_map_list("selecao_mapa_window", maps)
        elif new_state == "ranking":
            if not dpg.does_item_exist("ranking_window"):
                with dpg.window(tag="ranking_window", width=500, height=600, pos=[self.width//2-250, self.height//2-300]):
                    dpg.add_text("Ranking", tag="ranking_title")
                    self.add_voltar_button("ranking_window", lambda: self.change_state("menu_inicial"))
            dpg.configure_item("ranking_window", show=True)
            # Exibe ranking
            self.render_ranking("ranking_window", self.ranking_data)

    def process_events(self):
        if time.time() - self.last_resource_check > self.resource_check_interval:
            self.adjust_resources()
            self.last_resource_check = time.time()

    def update(self):
        dpg.render_dearpygui_frame()
        if dpg.is_dearpygui_running():
            dpg.set_viewport_vsync(True)
            dpg.set_frame_rate(self.fps_limit)

    def clear(self):
        self.pygame_screen.fill((255, 255, 255))

    def close(self):
        dpg.destroy_context()
        pygame.quit()

    def load_ranking_data(self, filename="ranking.json"):
        from interface_ranking import load_ranking
        self.ranking_data = load_ranking(filename)

    def save_ranking_data(self, filename="ranking.json"):
        from interface_ranking import save_ranking
        save_ranking(self.ranking_data, filename)

    def draw_corridor(self, corridor_rect):
        pygame.draw.rect(self.pygame_screen, (0, 0, 0), corridor_rect, 8)

    def draw_barriers(self, barriers):
        if barriers:
            for bx, by, bw, bh in barriers:
                pygame.draw.rect(self.pygame_screen, (100, 100, 100), pygame.Rect(bx, by, bw, bh))

    def draw_checkpoints(self, checkpoints, success_idx=None):
        t = time.time()
        for i, cp in enumerate(checkpoints):
            if success_idx is not None and i == success_idx:
                raio = int(10 * ENV_SCALE * (1 + 0.5 * math.sin(t*4)))
                cor = (0, int(255 * abs(math.sin(t*2))), 0)
            else:
                raio = int(10 * ENV_SCALE)
                cor = (0, 255, 0)
            pygame.draw.circle(self.pygame_screen, cor, (int(cp[0]), int(cp[1])), raio)

    def draw_car(self, pos, angle, color=(255,0,0,128), show=True, traj=None):
        if not show:
            return
        if not hasattr(self, 'last_car_pos') or self.last_car_pos is None:
            self.last_car_pos = [float(pos[0]), float(pos[1])]
        dt = self.clock.get_time() / 16.67
        interp_pos = [
            self.last_car_pos[0] + (pos[0] - self.last_car_pos[0]) * min(dt, 1.0),
            self.last_car_pos[1] + (pos[1] - self.last_car_pos[1]) * min(dt, 1.0)
        ]
        if traj and len(traj) > 1:
            pontos = [(int(float(x)), int(float(y))) for x, y in traj if isinstance(x, (int, float)) and isinstance(y, (int, float))]
            n = len(pontos)
            for i in range(1, n):
                age = n - i
                fade = max(0, 255 - age * 10)
                cor = (255, 0, 0, fade)
                s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                pygame.draw.line(s, cor, pontos[i-1], pontos[i], 2)
                self.pygame_screen.blit(s, (0,0))
        car_surf = pygame.Surface((int(40*ENV_SCALE), int(20*ENV_SCALE)), pygame.SRCALPHA)
        car_surf.fill(color)
        car_rot = pygame.transform.rotate(car_surf, angle)
        rect = car_rot.get_rect(center=(int(interp_pos[0]), int(interp_pos[1])))
        self.pygame_screen.blit(car_rot, rect.topleft)
        self.last_car_pos = [float(pos[0]), float(pos[1])]

    def draw_car_grid(self, pos, angle, idx, color=(255,0,0)):
        col = idx % self.grid_cols
        row = idx // self.grid_rows
        offset_x = col * self.cell_width
        offset_y = row * self.cell_height
        car_surf = pygame.Surface((int(40*ENV_SCALE), int(20*ENV_SCALE)), pygame.SRCALPHA)
        car_surf.fill(color)
        car_rot = pygame.transform.rotate(car_surf, angle)
        rect = car_rot.get_rect(center=(int(pos[0])+offset_x, int(pos[1])+offset_y))
        self.pygame_screen.blit(car_rot, rect.topleft)

    def draw_dashboard(self, rewards_hist, collisions_hist, penalties_hist, ciclo, avg_speed, n_dif):
        self.dashboard.draw_dashboard(
            rewards_hist, collisions_hist, penalties_hist, ciclo, avg_speed, n_dif,
            self.fase_desc, self.n_parallel, self.checkpoints
        )

    def show_agent_form(self, on_submit, agent_data=None):
        """Exibe um formulário gráfico para criar ou editar agente.
        on_submit: função callback que recebe dict com os dados preenchidos.
        agent_data: dict opcional com dados para edição.
        """
        import dearpygui.dearpygui as dpg
        if dpg.does_item_exist("agent_form_window"):
            dpg.delete_item("agent_form_window")
        nome_default = agent_data["nome"] if agent_data and "nome" in agent_data else ""
        tipo_default = agent_data["tipo"] if agent_data and "tipo" in agent_data else "DQN"
        with dpg.window(label="Agente", tag="agent_form_window", modal=True, width=400, height=250, pos=[self.width//2-200, self.height//2-125]):
            dpg.add_text("Nome do agente:")
            nome_id = dpg.add_input_text(default_value=nome_default, tag="agent_nome_input", width=300)
            dpg.add_text("Tipo de agente:")
            tipo_id = dpg.add_combo(["DQN", "PPO", "SAC"], default_value=tipo_default, tag="agent_tipo_combo", width=150)
            def submit_callback():
                nome = dpg.get_value(nome_id).strip()
                tipo = dpg.get_value(tipo_id).strip().upper()
                if not nome or tipo not in ["DQN", "PPO", "SAC"]:
                    dpg.add_text("Preencha nome e tipo válidos!", parent="agent_form_window")
                    return
                dpg.delete_item("agent_form_window")
                on_submit({"nome": nome, "tipo": tipo})
            dpg.add_button(label="Salvar", callback=submit_callback)
            dpg.add_button(label="Cancelar", callback=lambda: dpg.delete_item("agent_form_window"))

    def add_voltar_button(self, parent_tag, callback):
        import dearpygui.dearpygui as dpg
        dpg.add_button(label="Voltar", width=80, callback=callback, parent=parent_tag, pos=[10, 10])

    def show_message(self, message, success=True):
        import dearpygui.dearpygui as dpg
        color = (60, 180, 80) if success else (220, 80, 80)
        if dpg.does_item_exist("msg_popup"): dpg.delete_item("msg_popup")
        with dpg.window(label="Mensagem", tag="msg_popup", modal=True, width=350, height=120, pos=[self.width//2-175, self.height//2-60]):
            dpg.add_text(message, color=color)
            dpg.add_button(label="OK", width=80, callback=lambda: dpg.delete_item("msg_popup"))

    def render_agent_list(self, parent_tag, agents):
        import dearpygui.dearpygui as dpg
        if dpg.does_item_exist("agent_list_group"): dpg.delete_item("agent_list_group")
        with dpg.group(parent=parent_tag, tag="agent_list_group"):
            for ag in agents:
                dpg.add_text(f"{ag['nome']} ({ag['tipo']})", bullet=True)

    def render_map_list(self, parent_tag, maps):
        import dearpygui.dearpygui as dpg
        if dpg.does_item_exist("map_list_group"): dpg.delete_item("map_list_group")
        with dpg.group(parent=parent_tag, tag="map_list_group"):
            for mp in maps:
                dpg.add_text(mp, bullet=True)

    def render_ranking(self, parent_tag, ranking_data):
        import dearpygui.dearpygui as dpg
        if dpg.does_item_exist("ranking_group"): dpg.delete_item("ranking_group")
        with dpg.group(parent=parent_tag, tag="ranking_group"):
            for key, val in ranking_data.items():
                dpg.add_text(f"{key}: Score={val['score']:.1f}, Vel={val['speed']:.1f}, Tempo={val['tempo']:.1f}s", bullet=True)