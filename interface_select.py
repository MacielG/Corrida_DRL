# interface_select.py
import pygame
import os
import math
import time
from interface_assets import load_icon
from interface_agents import load_agents, AgentInfo

class SelectScreen:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.agente_btns = []
        self.mapa_btns = []
        self.scroll_y = 0

    def draw_selecao_agente(self, screen, selected_agent=None, selected_map=None):
        # Fundo Moderno (Dark Blue Gradient)
        bg = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            # Gradiente azul escuro para preto
            color_val = max(0, 20 - int(y * 0.02))
            pygame.draw.line(bg, (10, 15 + int(y*0.05), 30 + int(y*0.08)), (0, y), (self.width, y))
        screen.blit(bg, (0,0))

        # Título
        font_title = pygame.font.SysFont('Segoe UI', 48, bold=True)
        title = font_title.render("Selecione seu Piloto", True, (255, 255, 255))
        screen.blit(title, (self.width//2 - title.get_width()//2, 40))

        # Carregar Agentes Reais
        agents_data = load_agents()
        
        if not agents_data:
            font_warn = pygame.font.SysFont('Segoe UI', 28, bold=True)
            font_inst = pygame.font.SysFont('Segoe UI', 20)
            
            warn = font_warn.render("Nenhum agente criado!", True, (255, 150, 100))
            inst = font_inst.render("Pressione ESC para voltar. Crie um agente em 'Gestao de Agentes'", True, (200, 200, 200))
            
            screen.blit(warn, (self.width//2 - warn.get_width()//2, self.height//2 - 50))
            screen.blit(inst, (self.width//2 - inst.get_width()//2, self.height//2 + 30))
            self.agente_btns = []
            pygame.display.flip()
            return

        self.agente_btns = []
        mx, my = pygame.mouse.get_pos()
        
        # Grid de cards
        cols = 3
        card_w, card_h = 220, 280
        gap_x, gap_y = 40, 40
        start_x = (self.width - (cols * card_w + (cols-1) * gap_x)) // 2
        start_y = 140

        for i, ag_dict in enumerate(agents_data):
            ag = AgentInfo.from_dict(ag_dict)
            col = i % cols
            row = i // cols
            
            x = start_x + col * (card_w + gap_x)
            y = start_y + row * (card_h + gap_y)
            
            rect = pygame.Rect(x, y, card_w, card_h)
            self.agente_btns.append((ag.nome, rect)) # Salva o NOME do agente

            is_hover = rect.collidepoint(mx, my)
            is_selected = (selected_agent == ag.nome)

            # Desenho do Card
            # Sombra
            shadow_rect = rect.copy()
            shadow_rect.x += 6
            shadow_rect.y += 6
            pygame.draw.rect(screen, (0,0,0,100), shadow_rect, border_radius=15)

            # Fundo do card
            if is_selected:
                color = (50, 100, 180) # Azul selecionado
                border_c = (255, 255, 255)
            elif is_hover:
                color = (40, 50, 70) # Cinza hover
                border_c = (100, 200, 255)
            else:
                color = (30, 35, 45) # Escuro padrão
                border_c = (60, 70, 80)

            pygame.draw.rect(screen, color, rect, border_radius=15)
            pygame.draw.rect(screen, border_c, rect, 2, border_radius=15)

            # Ícone
            icon_path = f"assets/{ag.tipo.lower()}_icon.png"
            icon = load_icon(icon_path, size=(80,80))
            if icon:
                screen.blit(icon, (x + card_w//2 - 40, y + 20))
            
            # Textos
            font_name = pygame.font.SysFont('Segoe UI', 28, bold=True)
            font_info = pygame.font.SysFont('Segoe UI', 18)
            
            name_surf = font_name.render(ag.nome, True, (255,255,255))
            type_surf = font_info.render(f"Algoritmo: {ag.tipo}", True, (180,180,180))
            lvl_surf = font_info.render(f"Nível: {ag.level}", True, (255, 200, 50))
            xp_surf = font_info.render(f"XP: {sum(h.get('xp_gained',0) for h in ag.historico)}", True, (150,150,150))

            screen.blit(name_surf, (x + card_w//2 - name_surf.get_width()//2, y + 110))
            screen.blit(type_surf, (x + 15, y + 160))
            screen.blit(lvl_surf, (x + 15, y + 190))
            screen.blit(xp_surf, (x + 15, y + 220))

            if is_selected:
                chk_font = pygame.font.SysFont('Segoe UI', 20, bold=True)
                chk = chk_font.render("SELECIONADO", True, (100, 255, 100))
                screen.blit(chk, (x + card_w//2 - chk.get_width()//2, y + 250))

        pygame.display.flip()

    def draw_selecao_mapa(self, screen, selected_map=None):
        # Fundo Gradiente
        bg = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            pygame.draw.line(bg, (15, 20 + int(y*0.03), 40 + int(y*0.05)), (0, y), (self.width, y))
        screen.blit(bg, (0,0))

        font = pygame.font.SysFont('Segoe UI', 48, bold=True)
        title = font.render("Selecione o Mapa", True, (255,255,255))
        screen.blit(title, (self.width//2 - title.get_width()//2, 50))
        
        mapas = ["corridor", "curve", "circle"]
        nomes_mapas = {"corridor": "Corredor Reto", "curve": "Pista Curva", "circle": "Circular"}
        
        self.mapa_btns = []
        mx, my = pygame.mouse.get_pos()
        
        start_y = 180
        btn_h = 100
        btn_w = 600
        
        for i, mp in enumerate(mapas):
            rect = pygame.Rect((self.width - btn_w)//2, start_y + i*130, btn_w, btn_h)
            self.mapa_btns.append((mp, rect))
            
            is_hover = rect.collidepoint(mx, my)
            is_selected = (selected_map == mp)
            
            color = (50, 120, 80) if is_selected else ((60, 70, 90) if is_hover else (40, 45, 55))
            border = (100, 255, 150) if is_selected else ((200,200,255) if is_hover else (80,80,80))
            
            pygame.draw.rect(screen, color, rect, border_radius=12)
            pygame.draw.rect(screen, border, rect, 3, border_radius=12)
            
            font_btn = pygame.font.SysFont('Segoe UI', 36)
            txt = font_btn.render(nomes_mapas.get(mp, mp), True, (255,255,255))
            screen.blit(txt, (rect.x + 40, rect.y + 25))
            
            if is_selected:
                pygame.draw.circle(screen, (100, 255, 100), (rect.right - 50, rect.centery), 15)

        pygame.display.flip()

    def handle_selecao_agente_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for ag_nome, rect in self.agente_btns:
                    if rect.collidepoint(mx, my):
                        return ag_nome # Retorna o nome real do agente (ex: "Racer1")
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
        return None # Retorno padrão

    def handle_selecao_mapa_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for mp, rect in self.mapa_btns:
                    if rect.collidepoint(mx, my):
                        return mp
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
