import pygame

class RankingScreen:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font_title = pygame.font.SysFont('Segoe UI', 48, bold=True)
        self.font_entry = pygame.font.SysFont('Segoe UI', 28)
        self.margin_top = 80
        self.line_height = 40

    def draw_ranking(self, screen, ranking_data=None, highlight_idx=None):
        # Fundo gradiente
        bg = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(self.height):
            cor = (240-int(30*y/self.height), 244-int(20*y/self.height), 255-int(10*y/self.height), 255)
            pygame.draw.line(bg, cor, (0, y), (self.width, y))
        screen.blit(bg, (0,0))
        # Sombra da tabela
        table_rect = pygame.Rect(40, self.margin_top-10, self.width-80, 25+self.line_height*22)
        sombra = pygame.Surface((table_rect.width, table_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(sombra, (80,120,180,60), (6,6,table_rect.width-12,table_rect.height-12), border_radius=18)
        screen.blit(sombra, (table_rect.x-3, table_rect.y-3))
        # Cabeçalho
        title_surf = self.font_title.render("Ranking", True, (30, 60, 120))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 20))
        y = self.margin_top
        header = self.font_entry.render(f"{'Pos':<4} {'Agente|Mapa':<20} {'Score':>8} {'Velocidade':>12} {'Tempo':>10}", True, (255,255,255))
        header_bg = pygame.Surface((self.width-80, self.line_height), pygame.SRCALPHA)
        pygame.draw.rect(header_bg, (74,144,226,220), (0,0,self.width-80,self.line_height), border_radius=12)
        screen.blit(header_bg, (50, y))
        screen.blit(header, (60, y+4))
        y += self.line_height
        # Dados
        if ranking_data is None or not ranking_data:
            no_data_surf = self.font_entry.render("Nenhum dado de ranking disponível.", True, (100, 100, 100))
            screen.blit(no_data_surf, (self.width // 2 - no_data_surf.get_width() // 2, y+30))
        else:
            sorted_items = sorted(ranking_data.items(), key=lambda x: x[1].get("score", 0), reverse=True)
            anim_offset = 40  # Para animação de entrada
            for idx, (key, val) in enumerate(sorted_items[:20], start=1):
                score = val.get("score", 0)
                speed = val.get("speed", 0)
                tempo = val.get("tempo", 0)
                entry_text = f"{idx:<4} {key:<20} {score:>8.2f} {speed:>12.2f} {tempo:>10.2f}s"
                # Linhas alternadas
                row_bg = pygame.Surface((self.width-80, self.line_height), pygame.SRCALPHA)
                cor_bg = (255,255,255,220) if idx%2==0 else (230,240,255,220)
                if highlight_idx is not None and idx == highlight_idx:
                    # Pisca azul
                    t = pygame.time.get_ticks()//100 % 2
                    cor_bg = (120,180,255,220) if t==0 else (74,144,226,220)
                pygame.draw.rect(row_bg, cor_bg, (0,0,self.width-80,self.line_height), border_radius=8)
                # Animação de entrada: desliza de baixo para cima
                slide = max(0, anim_offset - idx*4)
                screen.blit(row_bg, (50, y+slide))
                entry_surf = self.font_entry.render(entry_text, True, (30, 60, 120))
                screen.blit(entry_surf, (60, y+4+slide))
                y += self.line_height
        pygame.display.flip()
