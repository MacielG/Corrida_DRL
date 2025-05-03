# interface_select.py
import pygame
import os
from interface_assets import load_icon

class SelectScreen:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.agente_btns = []
        self.mapa_btns = []

    def draw_selecao_agente(self, screen, selected_agent=None, selected_map=None):
        # Fundo gradiente animado
        bg = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(self.height):
            cor = (220-int(40*y/self.height), 240-int(30*y/self.height), 255-int(15*y/self.height), 230)
            pygame.draw.line(bg, cor, (0, y), (self.width, y))
        screen.blit(bg, (0,0))
        font = pygame.font.SysFont('Roboto', 40, bold=True)
        title = font.render("Selecione o Agente", True, (30,60,120))
        screen.blit(title, (self.width//2 - title.get_width()//2, 70))
        agentes = ["DQN", "PPO", "SAC"]
        icones = {"DQN": "assets/dqn_icon.png", "PPO": "assets/ppo_icon.png", "SAC": "assets/sac_icon.png"}
        self.agente_btns = []
        mx, my = pygame.mouse.get_pos()
        for i, ag in enumerate(agentes):
            rect = (self.width//2-220 + i*180, 220, 150, 150)
            r = pygame.Rect(rect)
            is_hover = r.collidepoint(mx,my)
            is_selected = selected_agent==ag
            # Animação de hover/seleção
            scale = 1.1 if is_hover else (1.05 if is_selected else 1.0)
            surf = pygame.Surface((150,150), pygame.SRCALPHA)
            cor_card = (120,220,255,220) if is_hover or is_selected else (255,255,255,200)
            pygame.draw.rect(surf, cor_card, (0,0,150,150), border_radius=24)
            sombra = pygame.Surface((150,150), pygame.SRCALPHA)
            pygame.draw.rect(sombra, (80,120,180,60), (6,6,138,138), border_radius=28)
            screen.blit(sombra, (rect[0]-3, rect[1]-3))
            # Ícone
            if os.path.exists(icones[ag]):
                icon = pygame.image.load(icones[ag]).convert_alpha()
                icon = pygame.transform.smoothscale(icon, (60,60))
                surf.blit(icon, (45,20))
            # Nome
            ag_text = font.render(ag, True, (30,60,120))
            surf.blit(ag_text, (35, 90))
            # Status
            model_path = f"models/model_{selected_map or 'corridor'}_{ag}_step_10000.zip"
            status = "Treinado" if os.path.exists(model_path) else "Novo"
            status_color = (80,200,120) if status=="Treinado" else (200,160,60)
            status_font = pygame.font.SysFont('Roboto', 22, bold=True)
            st = status_font.render(status, True, status_color)
            surf.blit(st, (35, 125))
            # Escala animada
            surf = pygame.transform.smoothscale(surf, (int(150*scale), int(150*scale)))
            screen.blit(surf, (rect[0]-(surf.get_width()-150)//2, rect[1]-(surf.get_height()-150)//2))
            # Borda animada
            if is_selected:
                pygame.draw.rect(screen, (74,144,226), pygame.Rect(rect[0]-4, rect[1]-4, 158, 158), 4, border_radius=28)
            elif is_hover:
                pygame.draw.rect(screen, (120,180,255), pygame.Rect(rect[0]-2, rect[1]-2, 154, 154), 3, border_radius=26)
            self.agente_btns.append((ag, rect))
            # Tooltip
            if is_hover:
                tip_font = pygame.font.SysFont('Open Sans', 20)
                tip = f"{ag}: {'Treinado' if status=='Treinado' else 'Novo'}"
                tip_surf = tip_font.render(tip, True, (40,60,120))
                screen.blit(tip_surf, (mx+20, my-10))
        pygame.display.flip()

    def draw_selecao_mapa(self, screen, selected_map=None):
        # Fundo gradiente animado
        bg = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(self.height):
            cor = (220-int(40*y/self.height), 255-int(20*y/self.height), 220-int(40*y/self.height), 230)
            pygame.draw.line(bg, cor, (0, y), (self.width, y))
        screen.blit(bg, (0,0))
        font = pygame.font.SysFont('Roboto', 40, bold=True)
        title = font.render("Selecione o Mapa", True, (30,60,120))
        screen.blit(title, (self.width//2 - title.get_width()//2, 70))
        mapas = ["corridor", "curve", "circle"]
        icones = {"corridor": "assets/play.png", "curve": "assets/ranking.png", "circle": "assets/exit.jpg"}
        self.mapa_btns = []
        mx, my = pygame.mouse.get_pos()
        for i, mp in enumerate(mapas):
            rect = (self.width//2-220 + i*180, 220, 150, 150)
            r = pygame.Rect(rect)
            is_hover = r.collidepoint(mx,my)
            is_selected = selected_map==mp
            scale = 1.1 if is_hover else (1.05 if is_selected else 1.0)
            surf = pygame.Surface((150,150), pygame.SRCALPHA)
            cor_card = (180,255,200,220) if is_hover or is_selected else (255,255,255,200)
            pygame.draw.rect(surf, cor_card, (0,0,150,150), border_radius=24)
            sombra = pygame.Surface((150,150), pygame.SRCALPHA)
            pygame.draw.rect(sombra, (80,120,180,60), (6,6,138,138), border_radius=28)
            screen.blit(sombra, (rect[0]-3, rect[1]-3))
            # Ícone
            if os.path.exists(icones[mp]):
                icon = pygame.image.load(icones[mp]).convert_alpha()
                icon = pygame.transform.smoothscale(icon, (60,60))
                surf.blit(icon, (45,20))
            mp_text = font.render(mp, True, (30,60,120))
            surf.blit(mp_text, (35, 90))
            surf = pygame.transform.smoothscale(surf, (int(150*scale), int(150*scale)))
            screen.blit(surf, (rect[0]-(surf.get_width()-150)//2, rect[1]-(surf.get_height()-150)//2))
            if is_selected:
                pygame.draw.rect(screen, (74,144,226), pygame.Rect(rect[0]-4, rect[1]-4, 158, 158), 4, border_radius=28)
            elif is_hover:
                pygame.draw.rect(screen, (120,180,255), pygame.Rect(rect[0]-2, rect[1]-2, 154, 154), 3, border_radius=26)
            self.mapa_btns.append((mp, rect))
            if is_hover:
                tip_font = pygame.font.SysFont('Open Sans', 20)
                tip = f"{mp.title()}"
                tip_surf = tip_font.render(tip, True, (40,60,120))
                screen.blit(tip_surf, (mx+20, my-10))
        pygame.display.flip()

    def handle_selecao_agente_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for ag, rect in self.agente_btns:
                    r = pygame.Rect(rect)
                    if r.collidepoint(mx, my):
                        return ag
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None

    def handle_selecao_mapa_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for mp, rect in self.mapa_btns:
                    r = pygame.Rect(rect)
                    if r.collidepoint(mx, my):
                        return mp
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
