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

def draw_gestao_agentes(screen, width, height, agents, gestao_btn_novo, gestao_agent_cards):
    # Fundo gradiente
    bg = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        cor = (255-int(60*y/height), 245-int(40*y/height), 220-int(80*y/height), 255)
        pygame.draw.line(bg, cor, (0, y), (width, y))
    screen.blit(bg, (0,0))
    font = pygame.font.SysFont('Roboto', 44, bold=True)
    title = font.render("Gestão de Agentes", True, (30,60,120))
    screen.blit(title, (width//2 - title.get_width()//2, 40))
    # Botão novo agente
    btn_font = pygame.font.SysFont('Roboto', 32)
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

def handle_gestao_agentes_events(events, gestao_btn_novo, gestao_agent_cards, agents, interface=None):
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            if gestao_btn_novo and gestao_btn_novo[0].collidepoint(mx, my):
                if interface:
                    criar_novo_agente(agents, interface)
                return
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
                    comprar_upgrade(ag.to_dict() if isinstance(ag, AgentInfo) else ag)
                    # Recarrega agents pois foram modificados
                    agents = load_agents()
                    return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "escape"

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

def criar_novo_agente(agents, interface):
     """Cria um novo agente (CLI simplificado)."""
     print("\n" + "="*60)
     print("CRIAR NOVO AGENTE")
     print("="*60)
     
     try:
         nome = input("Nome do agente: ").strip()
         if not nome:
             print("Erro: Nome não pode ser vazio!")
             return
         
         if any((ag["nome"] if isinstance(ag, dict) else ag.nome) == nome for ag in agents):
             print(f"Erro: Já existe agente com nome '{nome}'!")
             return
         
         print("\nTipos disponíveis:")
         tipos = ["carro_rapido", "carro_equilibrado", "carro_cauteloso"]
         for i, t in enumerate(tipos, 1):
             print(f"  {i}. {t}")
         
         tipo_choice = input("Escolha o tipo (número): ").strip()
         tipo_idx = int(tipo_choice) - 1
         
         if 0 <= tipo_idx < len(tipos):
             tipo = tipos[tipo_idx]
             ag = AgentInfo(nome, tipo)
             agents.append(ag.to_dict())
             save_agents(agents)
             play_sound("clique")
             print(f"\n✓ Agente '{nome}' ({tipo}) criado com sucesso!")
         else:
             print("Erro: Tipo inválido!")
     except Exception as e:
         print(f"Erro ao criar agente: {e}")

def editar_agente(ag, interface):
     """Edita um agente existente (CLI simplificado)."""
     ag_dict = ag.to_dict() if isinstance(ag, AgentInfo) else ag
     print("\n" + "="*60)
     print(f"EDITAR AGENTE: {ag_dict['nome']}")
     print("="*60)
     
     try:
         novo_nome = input(f"Novo nome [{ag_dict['nome']}]: ").strip() or ag_dict['nome']
         
         print("\nTipos disponíveis:")
         tipos = ["carro_rapido", "carro_equilibrado", "carro_cauteloso"]
         for i, t in enumerate(tipos, 1):
             print(f"  {i}. {t}")
         
         tipo_choice = input(f"Novo tipo [1-3, atual: {ag_dict['tipo']}]: ").strip()
         if tipo_choice:
             tipo_idx = int(tipo_choice) - 1
             if 0 <= tipo_idx < len(tipos):
                 novo_tipo = tipos[tipo_idx]
             else:
                 print("Erro: Tipo inválido!")
                 return
         else:
             novo_tipo = ag_dict['tipo']
         
         ag_dict["nome"] = novo_nome
         ag_dict["tipo"] = novo_tipo
         
         agents = load_agents()
         for a in agents:
             if a["nome"] == novo_nome:
                 a.update(ag_dict)
                 break
         
         save_agents(agents)
         play_sound("clique")
         print(f"\n✓ Agente '{novo_nome}' editado com sucesso!")
     except Exception as e:
         print(f"Erro ao editar agente: {e}")

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

def comprar_upgrade(agent_dict):
    """Menu simples para comprar upgrades com XP"""
    from gamification import GamificationSystem
    
    agent = AgentInfo.from_dict(agent_dict)
    total_xp = sum(h.get('xp_gained', 0) for h in agent.historico)
    
    print("\n" + "="*60)
    print(f"UPGRADES - {agent.nome} (Nível {agent.level}, {total_xp} XP)")
    print("="*60)
    
    upgrades = GamificationSystem.get_upgrades_available(agent)
    
    for i, upgrade in enumerate(upgrades, 1):
        status = "✓ Disponível" if upgrade['disponivel'] else "✗ Não disponível"
        print(f"\n{i}. {upgrade['nome']} - {upgrade['custo_xp']} XP [{status}]")
        print(f"   {upgrade['descricao']}")
        print(f"   Valor atual: {agent.stats[upgrade['id']]:.2f}")
    
    print(f"\n0. Voltar")
    print("="*60)
    
    # Em modo CLI, pediremos input
    try:
        choice = input("Escolha o upgrade (número): ").strip()
        choice_idx = int(choice) - 1
        
        if choice == "0":
            return False
        
        if 0 <= choice_idx < len(upgrades):
            upgrade_id = upgrades[choice_idx]['id']
            success, msg = GamificationSystem.apply_upgrade(agent, upgrade_id)
            
            if success:
                print(f"\n✓ {msg}")
                print(f"  Novo nível: {agent.level}")
                print(f"  Novo valor de {upgrade_id}: {agent.stats[upgrade_id]:.2f}")
                
                # Atualiza JSON
                agents = load_agents()
                for a in agents:
                    if a["nome"] == agent.nome:
                        a.update(agent.to_dict())
                save_agents(agents)
                play_sound("finish")
                return True
            else:
                print(f"\n✗ {msg}")
                return False
        else:
            print("\nOpção inválida!")
            return False
    except ValueError:
        print("\nOpção inválida!")
        return False
    except Exception as e:
        print(f"\nErro: {e}")
        return False
