import pygame
import os
import json
from interface_assets import load_icon, play_sound

class AgentInfo:
    def __init__(self, nome, tipo, tempo_acumulado=0.0, modelo_path=None, historico=None, cor=(120,180,255), stats=None, level=1):
        self.nome = nome
        self.tipo = tipo
        self.tempo_acumulado = tempo_acumulado
        self.modelo_path = modelo_path or f"models/{nome}_{tipo}.zip"
        self.historico = historico or []
        self.cor = cor
        self.level = level
        # Stats padrão: Aceleração, Turn, MaxSpeed
        self.stats = stats or {"accel": 0.5, "turn_speed": 5.0, "max_speed": 20.0}
    
    def to_dict(self):
        return {
            "nome": self.nome,
            "tipo": self.tipo,
            "tempo_acumulado": self.tempo_acumulado,
            "modelo_path": self.modelo_path,
            "historico": self.historico,
            "cor": self.cor,
            "level": self.level,
            "stats": self.stats
        }
    
    @staticmethod
    def from_dict(d):
        return AgentInfo(
            d["nome"], d["tipo"], d.get("tempo_acumulado",0.0), 
            d.get("modelo_path"), d.get("historico",[]), 
            tuple(d.get("cor",(120,180,255))),
            d.get("stats"),
            d.get("level", 1)
        )
    
    def upgrade(self, stat_name):
        """Sistema simples de upgrade de stats"""
        if stat_name == "accel":
            self.stats["accel"] = min(self.stats["accel"] + 0.05, 1.0)
        elif stat_name == "turn_speed":
            self.stats["turn_speed"] = min(self.stats["turn_speed"] + 0.5, 15.0)
        elif stat_name == "max_speed":
            self.stats["max_speed"] = min(self.stats["max_speed"] + 1.0, 30.0)
        self.level += 1

def save_agents(agents, filename="agents.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(agents, f, ensure_ascii=False, indent=2)

def load_agents(filename="agents.json"):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Agent management UI methods moved from interface.py

from agent import Agent
import time

def draw_gestao_agentes(screen, width, height, agents, gestao_btn_novo, gestao_agent_cards, back_btn=None):
    # Fundo gradiente
    bg = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        cor = (255-int(60*y/height), 245-int(40*y/height), 220-int(80*y/height), 255)
        pygame.draw.line(bg, cor, (0, y), (width, y))
    screen.blit(bg, (0,0))
    font = pygame.font.SysFont('Roboto', 44, bold=True)
    title = font.render("Gestão de Agentes", True, (30,60,120))
    screen.blit(title, (width//2 - title.get_width()//2, 40))
    
    # Botão voltar (esquerda)
    btn_font = pygame.font.SysFont('Roboto', 32)
    btn_back = pygame.Rect(40, 40, 120, 50)
    pygame.draw.rect(screen, (200,120,120), btn_back, border_radius=16)
    screen.blit(btn_font.render("Voltar", True, (255,255,255)), (55, 55))
    gestao_agent_cards.clear()
    if back_btn is not None:
        back_btn.clear()
        back_btn.append(btn_back)
    
    # Botão novo agente (direita)
    btn_novo = pygame.Rect(width-220, 40, 180, 50)
    pygame.draw.rect(screen, (120,220,180), btn_novo, border_radius=16)
    screen.blit(btn_font.render("Novo Agente", True, (30,60,60)), (width-200, 55))
    gestao_btn_novo.clear()
    gestao_btn_novo.append(btn_novo)
    # Lista de agentes
    y = 120
    gestao_agent_cards.clear()
    mx, my = pygame.mouse.get_pos()
    for i, ag in enumerate(agents):
        # Converte AgentInfo para dicionário se necessário
        ag_dict = ag.to_dict() if isinstance(ag, AgentInfo) else ag
        
        # Animação de entrada: fade-in sequencial
        alpha = min(255, int((pygame.time.get_ticks() - i*100)/2))
        card = pygame.Surface((width-400, 90), pygame.SRCALPHA)
        cor_card = (220,230,245, alpha) if i%2==0 else (200,220,255, alpha)
        pygame.draw.rect(card, cor_card, (0,0,width-400,80), border_radius=18)
        sombra = pygame.Surface((width-400, 90), pygame.SRCALPHA)
        pygame.draw.rect(sombra, (80,120,180,60), (6,6,width-412,78), border_radius=22)
        card.blit(sombra, (0,0))
        # Ícone do agente
        icon = load_icon(f'assets/{ag_dict["tipo"].lower()}_icon.png', size=(48,48))
        card.blit(icon, (20, 20))
        # Nome e tipo
        nome_font = pygame.font.SysFont('Roboto', 30, bold=True)
        card.blit(nome_font.render(ag_dict["nome"], True, (30,60,120)), (80, 12))
        tipo_font = pygame.font.SysFont('Roboto', 22)
        card.blit(tipo_font.render(ag_dict["tipo"], True, (80,120,180)), (80, 45))
        # Tempo acumulado
        tempo = f"Tempo: {ag_dict['tempo_acumulado']:.1f}s"
        card.blit(tipo_font.render(tempo, True, (60,60,60)), (200, 45))
        
        # XP total (gamificação)
        total_xp = sum(h.get('xp_gained', 0) for h in ag_dict.get('historico', []))
        level = max(1, int(total_xp / 100) + 1)  # 1 nível a cada 100 XP
        xp_display = f"Nível {level} ({total_xp} XP)"
        card.blit(tipo_font.render(xp_display, True, (180,120,60)), (380, 12))
        
        # Status
        status = "Treinado" if os.path.exists(ag_dict.get("modelo_path","")) else "Novo"
        status_color = (80,200,120) if status=="Treinado" else (200,160,60)
        status_font = pygame.font.SysFont('Roboto', 20, bold=True)
        card.blit(status_font.render(status, True, status_color), (320, 45))
        # Botões: Selecionar, Editar, Excluir, Treinar, Upgrades
        btn_sel = pygame.Rect(card.get_width()-380, 20, 60, 40)
        btn_edit = pygame.Rect(card.get_width()-310, 20, 60, 40)
        btn_del = pygame.Rect(card.get_width()-240, 20, 60, 40)
        btn_train = pygame.Rect(card.get_width()-170, 20, 60, 40)
        btn_upgr = pygame.Rect(card.get_width()-100, 20, 80, 40)
        # Hover e ripple
        btns = [(btn_sel, (120,200,120), "Usar"), (btn_edit, (220,200,120), "Edit"), (btn_del, (220,120,120), "Del"), (btn_train, (120,120,220), "Train"), (btn_upgr, (180,120,220), "Upgrade")]
        for btn, cor, txt in btns:
            is_hover = btn.move(80, y).collidepoint(mx, my)
            cor_btn = tuple(min(255, c+30) for c in cor) if is_hover else cor
            pygame.draw.rect(card, cor_btn, btn, border_radius=10)
            card.blit(btn_font.render(txt, True, (255,255,255)), (btn.x+5, btn.y+5))
            # Ripple animado (simples)
            if is_hover and pygame.mouse.get_pressed()[0]:
                ripple = pygame.Surface((btn.width, btn.height), pygame.SRCALPHA)
                pygame.draw.ellipse(ripple, (255,255,255,80), (0,0,btn.width,btn.height))
                card.blit(ripple, (btn.x, btn.y))
        # Deslize/fade-out para exclusão (simulação, real seria animado ao excluir)
        screen.blit(card, (80, y))
        gestao_agent_cards.append({"rect": pygame.Rect(80, y, width-400, 80), "btn_sel": btn_sel.move(80, y), "btn_edit": btn_edit.move(80, y), "btn_del": btn_del.move(80, y), "btn_train": btn_train.move(80, y), "btn_upgr": btn_upgr.move(80, y), "idx": i})
        y += 100
    # Hover effect com brilho para card
    for card in gestao_agent_cards:
        if card["rect"].collidepoint(mx, my):
            glow_surf = pygame.Surface((card["rect"].width, card["rect"].height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (100, 100, 255, 60), glow_surf.get_rect(), border_radius=18)
            screen.blit(glow_surf, (card["rect"].x, card["rect"].y))
    pygame.display.flip()

def handle_gestao_agentes_events(events, gestao_btn_novo, gestao_agent_cards, agents, back_btn=None, interface=None):
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            
            # Verifica botão de voltar
            if back_btn and back_btn and back_btn[0].collidepoint(mx, my):
                return "back"
            
            # Verifica botão novo agente
            if gestao_btn_novo and gestao_btn_novo[0].collidepoint(mx, my):
                if interface:
                    criar_novo_agente(agents, interface)
                return
            
            # Verifica cards de agentes
            for card in gestao_agent_cards:
                ag = agents[card["idx"]]
                ag_name = ag.nome if isinstance(ag, AgentInfo) else ag["nome"]
                if card["btn_sel"].collidepoint(mx, my):
                    return ("select", ag_name)
                if card["btn_edit"].collidepoint(mx, my):
                    if interface:
                       editar_agente(ag, interface)
                    return
                if card["btn_del"].collidepoint(mx, my):
                    excluir_agente(ag)
                    return
                if card["btn_train"].collidepoint(mx, my):
                    treinar_agente(agents, card["idx"])
                    return
                if card["btn_upgr"].collidepoint(mx, my):
                    # Abre menu de compra de upgrades
                    ag_dict = ag.to_dict() if isinstance(ag, AgentInfo) else ag
                    interface.change_state("comprar_upgrade_agente")
                    interface.upgrade_agent_dict = ag_dict
                    interface.upgrade_selected_idx = 0
                    interface.upgrade_message = ""
                    from gamification import GamificationSystem
                    agent = AgentInfo.from_dict(ag_dict)
                    interface.upgrade_list = GamificationSystem.get_upgrades_available(agent)
                    return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "back"

def treinar_agente(agents, idx, map_type="corridor"):
     """Treina um agente específico com sistema de fases.
     
     Args:
         agents (list): Lista de agentes em dicionário.
         idx (int): Índice do agente a treinar.
         map_type (str): Tipo de mapa (corridor, curve, circle) - OBSOLETO, usa phase manager
     """
     ag_dict = agents[idx]
     ag = AgentInfo.from_dict(ag_dict)
     
     from environment import CorridaEnv
     from stable_baselines3.common.vec_env import DummyVecEnv
     from phase_manager import PhaseManager
     
     print(f"\n[TREINO] Iniciando treinamento de {ag.nome} com sistema de fases...")
     
     # 1. Carrega/cria o gerenciador de fases
     phase_mgr = PhaseManager(ag.nome)
     current_phase = phase_mgr.get_current_phase()
     
     print(f"[FASE] {current_phase.id+1}/4 - {current_phase.name}: {current_phase.description}")
     
     # 2. Cria ambiente com o mapa da fase atual
     def make_env():
         return CorridaEnv(map_type=current_phase.map_type, car_stats=ag.stats)
     
     env = DummyVecEnv([make_env for _ in range(4)])  # 4 ambientes paralelos
     
     # 3. Carrega/cria modelo
     model_path_base = ag.modelo_path.replace(".zip", "")
     agent = Agent(env, model_path=model_path_base, learning_rate=0.0003, gamma=0.98)
     
     if os.path.exists(ag.modelo_path):
         print(f"[TREINO] Carregando cérebro existente")
         agent.load(ag.modelo_path)
     else:
         print(f"[TREINO] Criando novo cérebro")
     
     # 4. Treina com feedback de progresso
     print("\n[TREINO] Executando episódios de treinamento...")
     episode_count = 0
     total_reward_episode = 0
     
     start_time = time.time()
     
     # Treina vários episódios até condição de sucesso
     max_episodes = current_phase.min_episodes_success + 10
     for ep in range(max_episodes):
         obs = env.reset()
         done = [False] * 4
         episode_rewards = [0] * 4
         episode_steps = [0] * 4
         
         while not all(done):
             actions, _ = agent.model.predict(obs, deterministic=False)
             obs, rewards, done, infos = env.step(actions)
             
             for i in range(4):
                 episode_rewards[i] += rewards[i]
                 episode_steps[i] += 1
         
         # Registra episódio
         avg_reward = sum(episode_rewards) / len(episode_rewards)
         avg_steps = sum(episode_steps) / len(episode_steps)
         success = avg_reward > current_phase.reward_threshold * 0.5
         
         phase_mgr.record_episode(avg_reward, success, avg_steps)
         episode_count += 1
         total_reward_episode = avg_reward
         
         print(f"  Ep {ep+1}/{max_episodes} | Recompensa: {avg_reward:+.1f} | Steps: {avg_steps:.0f} | {'✓' if success else '✗'}")
         
         # Verifica conclusão da fase
         if phase_mgr.check_phase_completion():
             print(f"\n[SUCESSO] Fase '{current_phase.name}' COMPLETA!")
             if phase_mgr.advance_phase():
                 new_phase = phase_mgr.get_current_phase()
                 print(f"[PROGRESSO] Próxima fase: {new_phase.name}")
             break
     
     elapsed = time.time() - start_time
     
     # 5. Atualiza estatísticas do agente
     ag.tempo_acumulado += elapsed
     xp_gained = int(episode_count * 10)  # 10 XP por episódio
     
     ag.historico.append({
         "timestamp": time.time(),
         "duration": elapsed,
         "map": current_phase.map_type,
         "episodes": episode_count,
         "xp_gained": xp_gained,
         "tipo_evento": "treino_fase",
         "phase_id": current_phase.id,
     })
     
     ag.historico = ag.historico[-50:]
     
     # 6. Salva
     ag_dict.update(ag.to_dict())
     agents[idx] = ag_dict
     save_agents(agents)
     agent.save(model_path_base)
     
     progress = phase_mgr.get_phase_progress()
     print(f"\n[TREINO] ✓ Completado em {elapsed:.1f}s ({episode_count} episódios)")
     print(f"         Taxa de sucesso: {progress['recent_success_rate']:.1%} | Recompensa média: {progress['avg_reward']:.1f}")
     print(f"         Fase atual: {progress['phase_name']} | Progresso: {'COMPLETA' if progress['completed'] else 'Em progresso'}")
     
     play_sound("finish")

def draw_criar_agente_dialog(screen, width, height, dialog_state, nome, selected_type, error_msg=""):
    """Desenha o diálogo de criação de novo agente (sem loop bloqueante)."""
    tipos = ["carro_rapido", "carro_equilibrado", "carro_cauteloso"]
    
    # Fundo
    screen.fill((240, 240, 250))
    
    # Título
    font_title = pygame.font.SysFont('Roboto', 48, bold=True)
    title = font_title.render("Novo Agente", True, (30, 60, 120))
    screen.blit(title, (width//2 - title.get_width()//2, 50))
    
    font_label = pygame.font.SysFont('Roboto', 28, bold=True)
    font_input = pygame.font.SysFont('Roboto', 24)
    font_small = pygame.font.SysFont('Roboto', 20)
    
    if dialog_state == "GET_NAME":
        # Entrada de nome
        label = font_label.render("Nome do Agente:", True, (30, 60, 120))
        screen.blit(label, (100, 150))
        
        input_box = pygame.Rect(100, 200, 600, 50)
        pygame.draw.rect(screen, (255, 255, 255), input_box)
        pygame.draw.rect(screen, (100, 150, 200), input_box, 3)
        
        texto = font_input.render(nome, True, (30, 30, 30))
        screen.blit(texto, (120, 215))
        
        # Cursor piscante
        cursor_timer = (pygame.time.get_ticks() // 250) % 2
        if cursor_timer == 0:
            cursor_x = 120 + texto.get_width()
            pygame.draw.line(screen, (0, 0, 0), (cursor_x, 210), (cursor_x, 240), 2)
        
        # Help text
        help_text = font_small.render("Digite o nome do agente (máx 20 caracteres)", True, (100, 100, 100))
        screen.blit(help_text, (100, 260))
        
        # Erro se houver
        if error_msg:
            error_surf = font_small.render(error_msg, True, (200, 50, 50))
            screen.blit(error_surf, (100, 300))
        
        # Instruções
        instr = font_small.render("ENTER: Continuar  |  ESC: Cancelar", True, (60, 60, 60))
        screen.blit(instr, (100, height - 80))
        
    elif dialog_state == "GET_TYPE":
        # Seleção de tipo
        label = font_label.render("Tipo de Carro:", True, (30, 60, 120))
        screen.blit(label, (100, 150))
        
        # Desenha opções
        start_y = 220
        for i, tipo in enumerate(tipos):
            is_selected = (i == selected_type)
            
            btn_rect = pygame.Rect(100, start_y + i*80, 600, 60)
            
            # Cor de fundo
            if is_selected:
                pygame.draw.rect(screen, (120, 200, 255), btn_rect)
                pygame.draw.rect(screen, (30, 60, 120), btn_rect, 4)
                cor_texto = (255, 255, 255)
            else:
                pygame.draw.rect(screen, (220, 230, 245), btn_rect)
                pygame.draw.rect(screen, (100, 150, 200), btn_rect, 2)
                cor_texto = (30, 60, 120)
            
            texto = font_input.render(f"{i+1}. {tipo.replace('_', ' ').title()}", True, cor_texto)
            screen.blit(texto, (130, start_y + i*80 + 15))
        
        # Instruções
        instr = font_small.render("CIMA/BAIXO: Selecionar  |  ENTER: Confirmar  |  ESC: Cancelar", True, (60, 60, 60))
        screen.blit(instr, (50, height - 80))

def draw_editar_agente_dialog(screen, width, height, dialog_state, ag_original, nome, selected_type, error_msg=""):
    """Desenha o diálogo de edição de agente (sem loop bloqueante)."""
    tipos = ["carro_rapido", "carro_equilibrado", "carro_cauteloso"]
    ag_dict = ag_original.to_dict() if isinstance(ag_original, AgentInfo) else ag_original
    
    # Fundo
    screen.fill((240, 240, 250))
    
    # Título
    font_title = pygame.font.SysFont('Roboto', 48, bold=True)
    title = font_title.render(f"Editar Agente: {ag_dict['nome']}", True, (30, 60, 120))
    screen.blit(title, (width//2 - title.get_width()//2, 50))
    
    font_label = pygame.font.SysFont('Roboto', 28, bold=True)
    font_input = pygame.font.SysFont('Roboto', 24)
    font_small = pygame.font.SysFont('Roboto', 20)
    
    if dialog_state == "GET_NAME":
        # Entrada de nome
        label = font_label.render("Novo Nome:", True, (30, 60, 120))
        screen.blit(label, (100, 150))
        
        input_box = pygame.Rect(100, 200, 600, 50)
        pygame.draw.rect(screen, (255, 255, 255), input_box)
        pygame.draw.rect(screen, (100, 150, 200), input_box, 3)
        
        texto = font_input.render(nome, True, (30, 30, 30))
        screen.blit(texto, (120, 215))
        
        # Cursor piscante
        cursor_timer = (pygame.time.get_ticks() // 250) % 2
        if cursor_timer == 0:
            cursor_x = 120 + texto.get_width()
            pygame.draw.line(screen, (0, 0, 0), (cursor_x, 210), (cursor_x, 240), 2)
        
        # Help text
        help_text = font_small.render(f"Nome atual: {ag_dict['nome']}", True, (100, 100, 100))
        screen.blit(help_text, (100, 260))
        
        # Instruções
        instr = font_small.render("ENTER: Continuar  |  ESC: Cancelar", True, (60, 60, 60))
        screen.blit(instr, (100, height - 80))
        
    elif dialog_state == "GET_TYPE":
        # Seleção de tipo
        label = font_label.render("Novo Tipo de Carro:", True, (30, 60, 120))
        screen.blit(label, (100, 150))
        
        current_tipo_text = font_small.render(f"Tipo atual: {ag_dict['tipo']}", True, (100, 100, 100))
        screen.blit(current_tipo_text, (100, 190))
        
        # Desenha opções
        start_y = 240
        for i, tipo in enumerate(tipos):
            is_selected = (i == selected_type)
            
            btn_rect = pygame.Rect(100, start_y + i*70, 600, 60)
            
            # Cor de fundo
            if is_selected:
                pygame.draw.rect(screen, (120, 200, 255), btn_rect)
                pygame.draw.rect(screen, (30, 60, 120), btn_rect, 4)
                cor_texto = (255, 255, 255)
            else:
                pygame.draw.rect(screen, (220, 230, 245), btn_rect)
                pygame.draw.rect(screen, (100, 150, 200), btn_rect, 2)
                cor_texto = (30, 60, 120)
            
            texto = font_input.render(f"{i+1}. {tipo.replace('_', ' ').title()}", True, cor_texto)
            screen.blit(texto, (130, start_y + i*70 + 12))
        
        # Instruções
        instr = font_small.render("CIMA/BAIXO: Selecionar  |  ENTER: Confirmar  |  ESC: Cancelar", True, (60, 60, 60))
        screen.blit(instr, (50, height - 80))

def criar_novo_agente(agents, interface):
      """Inicia o processo de criação de agente (muda estado da interface)."""
      interface.change_state("criar_agente")
      interface.criar_agente_state = "GET_NAME"
      interface.criar_agente_nome = ""
      interface.criar_agente_tipo = 0
      interface.criar_agente_error = ""

def editar_agente(ag, interface):
      """Inicia o processo de edição de agente (muda estado da interface)."""
      ag_dict = ag.to_dict() if isinstance(ag, AgentInfo) else ag
      interface.change_state("editar_agente")
      interface.editar_agente_state = "GET_NAME"
      interface.editar_agente_nome = ag_dict["nome"]
      interface.editar_agente_ag_original = ag
      
      tipos = ["carro_rapido", "carro_equilibrado", "carro_cauteloso"]
      try:
          interface.editar_agente_tipo = tipos.index(ag_dict["tipo"])
      except ValueError:
          interface.editar_agente_tipo = 0
      
      interface.editar_agente_error = ""

def handle_criar_agente_events(events, agents, interface):
    """Processa eventos do diálogo de criar novo agente."""
    tipos = ["carro_rapido", "carro_equilibrado", "carro_cauteloso"]
    
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        
        if event.type == pygame.KEYDOWN:
            if interface.criar_agente_state == "GET_NAME":
                if event.key == pygame.K_RETURN:
                    if interface.criar_agente_nome.strip():
                        # Verifica nome duplicado
                        if any((ag["nome"] if isinstance(ag, dict) else ag.nome) == interface.criar_agente_nome for ag in agents):
                            interface.criar_agente_error = "Erro: Agente com este nome já existe!"
                        else:
                            interface.criar_agente_state = "GET_TYPE"
                            interface.criar_agente_error = ""
                elif event.key == pygame.K_ESCAPE:
                    interface.change_state("gestao_agentes")
                elif event.key == pygame.K_BACKSPACE:
                    interface.criar_agente_nome = interface.criar_agente_nome[:-1]
                    interface.criar_agente_error = ""
                else:
                    if len(interface.criar_agente_nome) < 20 and event.unicode.isprintable():
                        interface.criar_agente_nome += event.unicode
                        interface.criar_agente_error = ""
            
            elif interface.criar_agente_state == "GET_TYPE":
                if event.key == pygame.K_UP:
                    interface.criar_agente_tipo = (interface.criar_agente_tipo - 1) % len(tipos)
                elif event.key == pygame.K_DOWN:
                    interface.criar_agente_tipo = (interface.criar_agente_tipo + 1) % len(tipos)
                elif event.key == pygame.K_RETURN:
                    # Criar agente
                    tipo = tipos[interface.criar_agente_tipo]
                    ag = AgentInfo(interface.criar_agente_nome, tipo)
                    agents.append(ag.to_dict())
                    save_agents(agents)
                    play_sound("clique")
                    interface.change_state("gestao_agentes")
                elif event.key == pygame.K_ESCAPE:
                    interface.change_state("gestao_agentes")

def handle_editar_agente_events(events, agents, interface):
    """Processa eventos do diálogo de editar agente."""
    tipos = ["carro_rapido", "carro_equilibrado", "carro_cauteloso"]
    
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        
        if event.type == pygame.KEYDOWN:
            if interface.editar_agente_state == "GET_NAME":
                if event.key == pygame.K_RETURN:
                    interface.editar_agente_state = "GET_TYPE"
                elif event.key == pygame.K_ESCAPE:
                    interface.change_state("gestao_agentes")
                elif event.key == pygame.K_BACKSPACE:
                    interface.editar_agente_nome = interface.editar_agente_nome[:-1]
                else:
                    if len(interface.editar_agente_nome) < 20 and event.unicode.isprintable():
                        interface.editar_agente_nome += event.unicode
            
            elif interface.editar_agente_state == "GET_TYPE":
                if event.key == pygame.K_UP:
                    interface.editar_agente_tipo = (interface.editar_agente_tipo - 1) % len(tipos)
                elif event.key == pygame.K_DOWN:
                    interface.editar_agente_tipo = (interface.editar_agente_tipo + 1) % len(tipos)
                elif event.key == pygame.K_RETURN:
                    # Atualizar agente
                    ag_dict = interface.editar_agente_ag_original.to_dict() if isinstance(interface.editar_agente_ag_original, AgentInfo) else interface.editar_agente_ag_original
                    novo_tipo = tipos[interface.editar_agente_tipo]
                    
                    agentes_loaded = load_agents()
                    for a in agentes_loaded:
                        if a["nome"] == ag_dict["nome"]:
                            a["nome"] = interface.editar_agente_nome
                            a["tipo"] = novo_tipo
                            break
                    
                    save_agents(agentes_loaded)
                    play_sound("clique")
                    interface.change_state("gestao_agentes")
                elif event.key == pygame.K_ESCAPE:
                    interface.change_state("gestao_agentes")

def excluir_agente(ag):
     agents = load_agents()
     ag_dict = ag.to_dict() if isinstance(ag, AgentInfo) else ag
     agents = [a for a in agents if a["nome"]!=ag_dict["nome"]]
     save_agents(agents)
     try:
         if ag_dict["modelo_path"] and os.path.exists(ag_dict["modelo_path"]):
             os.remove(ag_dict["modelo_path"])
     except Exception:
         pass
     play_sound("clique")

def draw_comprar_upgrade_dialog(screen, width, height, agent_dict, upgrades, selected_idx, message):
    """Desenha o diálogo de compra de upgrades (sem loop bloqueante)."""
    agent = AgentInfo.from_dict(agent_dict)
    total_xp = sum(h.get('xp_gained', 0) for h in agent.historico)
    
    # Fundo
    screen.fill((240, 240, 250))
    
    # Título
    font_title = pygame.font.SysFont('Roboto', 40, bold=True)
    title = font_title.render(f"Upgrades - {agent.nome}", True, (30, 60, 120))
    screen.blit(title, (width//2 - title.get_width()//2, 30))
    
    # Info do agente
    font_small = pygame.font.SysFont('Roboto', 18)
    info = font_small.render(f"Nível {agent.level} | {total_xp} XP", True, (100, 100, 100))
    screen.blit(info, (width//2 - info.get_width()//2, 80))
    
    font_label = pygame.font.SysFont('Roboto', 24, bold=True)
    font_content = pygame.font.SysFont('Roboto', 20)
    
    # Lista de upgrades
    start_y = 130
    item_height = 85
    
    for i, upgrade in enumerate(upgrades):
        is_selected = (i == selected_idx)
        
        # Posição
        y = start_y + i * item_height
        
        # Box
        box_rect = pygame.Rect(50, y, width - 100, item_height - 10)
        
        if is_selected:
            pygame.draw.rect(screen, (120, 200, 255), box_rect, border_radius=8)
            pygame.draw.rect(screen, (30, 60, 120), box_rect, 3, border_radius=8)
            cor_texto = (30, 60, 120)
        else:
            pygame.draw.rect(screen, (220, 230, 245), box_rect, border_radius=8)
            pygame.draw.rect(screen, (100, 150, 200), box_rect, 1, border_radius=8)
            cor_texto = (50, 50, 50)
        
        # Nome e custo
        status = "✓" if upgrade['disponivel'] else "✗"
        nome_text = f"{status} {upgrade['nome']} - {upgrade['custo_xp']} XP"
        nome_surf = font_label.render(nome_text, True, cor_texto)
        screen.blit(nome_surf, (70, y + 5))
        
        # Descrição
        desc_surf = font_content.render(upgrade['descricao'], True, cor_texto)
        screen.blit(desc_surf, (70, y + 35))
        
        # Valor atual
        valor_text = f"Valor atual: {agent.stats[upgrade['id']]:.2f}"
        valor_surf = font_small.render(valor_text, True, cor_texto)
        screen.blit(valor_surf, (70, y + 58))
    
    # Mensagem de status
    if message:
        msg_color = (100, 200, 100) if "sucesso" in message.lower() or "✓" in message else (200, 100, 100)
        msg_surf = font_small.render(message, True, msg_color)
        screen.blit(msg_surf, (width//2 - msg_surf.get_width()//2, height - 120))
    
    # Instruções
    instr = font_small.render("CIMA/BAIXO: Selecionar  |  ENTER: Comprar  |  ESC: Sair", True, (60, 60, 60))
    screen.blit(instr, (50, height - 70))

def handle_comprar_upgrade_events(events, interface):
    """Processa eventos do diálogo de compra de upgrades."""
    from gamification import GamificationSystem
    
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                interface.upgrade_selected_idx = (interface.upgrade_selected_idx - 1) % len(interface.upgrade_list)
            elif event.key == pygame.K_DOWN:
                interface.upgrade_selected_idx = (interface.upgrade_selected_idx + 1) % len(interface.upgrade_list)
            elif event.key == pygame.K_RETURN:
                if interface.upgrade_selected_idx < len(interface.upgrade_list):
                    upgrade = interface.upgrade_list[interface.upgrade_selected_idx]
                    if upgrade['disponivel']:
                        agent = AgentInfo.from_dict(interface.upgrade_agent_dict)
                        upgrade_id = upgrade['id']
                        success, msg = GamificationSystem.apply_upgrade(agent, upgrade_id)
                        
                        if success:
                            # Atualiza JSON
                            agents = load_agents()
                            for a in agents:
                                if a["nome"] == agent.nome:
                                    a.update(agent.to_dict())
                            save_agents(agents)
                            play_sound("finish")
                            interface.upgrade_message = f"✓ {msg}"
                            interface.upgrade_agent_dict = agent.to_dict()
                            # Recarrega upgrades
                            interface.upgrade_list = GamificationSystem.get_upgrades_available(agent)
                            interface.upgrade_selected_idx = min(interface.upgrade_selected_idx, len(interface.upgrade_list) - 1)
                        else:
                            interface.upgrade_message = f"✗ {msg}"
                    else:
                        interface.upgrade_message = "✗ Upgrade não disponível (XP insuficiente)"
            elif event.key == pygame.K_ESCAPE:
                interface.change_state("gestao_agentes")


