# interface_menu.py
import pygame
from interface_assets import load_icon, play_sound

class Menu:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.menu_btns = []

    def draw_menu_inicial(self, screen):
        screen.fill((255,255,255))
        bg = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            cor = (180-int(80*y/self.height), 210-int(60*y/self.height), 255-int(40*y/self.height))
            pygame.draw.line(bg, cor, (0, y), (self.width, y))
        screen.blit(bg, (0,0))
        font = pygame.font.SysFont('Segoe UI', 54, bold=True)
        title = font.render("Corrida DRL", True, (30,60,120))
        screen.blit(title, (self.width//2 - title.get_width()//2, 60))
        btn_font = pygame.font.SysFont('Segoe UI', 36)
        icon_names = ["play.png", "play.png", "ranking.png", "exit.png", "add_agent.png"]
        self.menu_btns = [
            ("Treinar agente", (self.width//2-140, 200, 280, 60)),
            ("Assistir corrida", (self.width//2-140, 280, 280, 60)),
            ("Ranking", (self.width//2-140, 360, 280, 60)),
            ("Sair", (self.width//2-140, 440, 280, 60)),
            ("Gestão de Agentes", (self.width//2-140, 520, 280, 60)),
        ]
        mx, my = pygame.mouse.get_pos()
        for i, (text, rect) in enumerate(self.menu_btns):
            r = pygame.Rect(rect)
            cor_btn = (120,180,255) if r.collidepoint(mx,my) else (220,230,245)
            pygame.draw.rect(screen, cor_btn, r, border_radius=18)
            pygame.draw.rect(screen, (80,120,180), r, 3, border_radius=18)
            icon = load_icon(f'assets/{icon_names[i]}', size=(40,40)) if i < len(icon_names) else None
            if icon:
                screen.blit(icon, (rect[0]+10, rect[1]+10))
            btn_text = btn_font.render(text, True, (30,60,120))
            screen.blit(btn_text, (rect[0]+60, rect[1]+13))
        if pygame.display.get_surface():
            pygame.display.flip()

    def handle_menu_events(self, state, menu_btns):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                play_sound("clique")
                mx, my = pygame.mouse.get_pos()
                for i, (_, rect) in enumerate(menu_btns):
                    r = pygame.Rect(rect)
                    if r.collidepoint(mx, my):
                        return i  # Retorna índice do botão clicado
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return -1
        return None

# Alias para compatibilidade com InterfaceDPG
InterfaceMenu = Menu
