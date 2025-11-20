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
        # Animação de entrada: fade-in sequencial
        alpha = min(255, int((pygame.time.get_ticks() - i*100)/2))
        card = pygame.Surface((width-400, 90), pygame.SRCALPHA)
        cor_card = (220,230,245, alpha) if i%2==0 else (200,220,255, alpha)
        pygame.draw.rect(card, cor_card, (0,0,width-400,80), border_radius=18)
        sombra = pygame.Surface((width-400, 90), pygame.SRCALPHA)
        pygame.draw.rect(sombra, (80,120,180,60), (6,6,width-412,78), border_radius=22)
        card.blit(sombra, (0,0))
        # Ícone do agente
        icon = load_icon(f'assets/{ag["tipo"].lower()}_icon.png', size=(48,48))
        card.blit(icon, (20, 20))
        # Nome e tipo
        nome_font = pygame.font.SysFont('Roboto', 30, bold=True)
        card.blit(nome_font.render(ag["nome"], True, (30,60,120)), (80, 12))
        tipo_font = pygame.font.SysFont('Roboto', 22)
        card.blit(tipo_font.render(ag["tipo"], True, (80,120,180)), (80, 45))
        # Tempo acumulado
        tempo = f"Tempo: {ag['tempo_acumulado']:.1f}s"
        card.blit(tipo_font.render(tempo, True, (60,60,60)), (200, 45))
        
        # XP total (gamificação)
        total_xp = sum(h.get('xp_gained', 0) for h in ag.get('historico', []))
        level = max(1, int(total_xp / 100) + 1)  # 1 nível a cada 100 XP
        xp_display = f"Nível {level} ({total_xp} XP)"
        card.blit(tipo_font.render(xp_display, True, (180,120,60)), (380, 12))
        
        # Status
        status = "Treinado" if os.path.exists(ag.get("modelo_path","")) else "Novo"
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
                if card["btn_sel"].collidepoint(mx, my):
                    return ("select", agents[card["idx"]]["nome"])
                if card["btn_edit"].collidepoint(mx, my):
                    if interface:
                        editar_agente(agents[card["idx"]], interface)
                    return
                if card["btn_del"].collidepoint(mx, my):
                    excluir_agente(agents[card["idx"]])
                    return
                if card["btn_train"].collidepoint(mx, my):
                    treinar_agente(agents, card["idx"])
                    return
                if card["btn_upgr"].collidepoint(mx, my):
                    # Abre menu de compra de upgrades
                    comprar_upgrade(agents[card["idx"]])
                    # Recarrega agents pois foram modificados
                    agents = load_agents()
                    return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "escape"

def treinar_agente(agents, idx, map_type="corridor"):
    """Treina um agente específico no mapa selecionado, carregando seu cérebro anterior.
    
    Args:
        agents (list): Lista de agentes em dicionário.
        idx (int): Índice do agente a treinar.
        map_type (str): Tipo de mapa (corridor, curve, circle).
    """
    ag_dict = agents[idx]
    ag = AgentInfo.from_dict(ag_dict)
    
    print(f"[TREINO] Iniciando treino de {ag.nome} no mapa '{map_type}'...")
    
    from environment import CorridaEnv
    from stable_baselines3.common.vec_env import DummyVecEnv
    
    # 1. Cria ambiente com o mapa correto
    # CORREÇÃO: Passa os stats (upgrades) do agente para o ambiente de treino
    def make_env():
        return CorridaEnv(map_type=map_type, car_stats=ag.stats)
    
    env = DummyVecEnv([make_env for _ in range(4)])  # 4 ambientes paralelos
    
    # 2. Instancia agente com o modelo_path correto
    # Remove extensão .zip para SB3 adicionar automaticamente
    model_path_base = ag.modelo_path.replace(".zip", "")
    agent = Agent(env, model_path=model_path_base, learning_rate=0.0003, gamma=0.98)
    
    # 3. Carrega modelo existente (continuidade/subjetivação) ou cria novo
    if os.path.exists(ag.modelo_path):
        print(f"[TREINO] Carregando cérebro existente de: {ag.modelo_path}")
        agent.load(ag.modelo_path)
    else:
        print(f"[TREINO] Criando novo cérebro para {ag.nome}")
    
    # 4. Treina por 20k passos (um 'round' de treino razoável para um jogo)
    start_time = time.time()
    agent.train(total_timesteps=20000)
    elapsed = time.time() - start_time
    
    # 5. Atualiza estatísticas do agente
    ag.tempo_acumulado += elapsed
    
    # Calcula score médio do treinamento (para XP)
    xp_gained = int(elapsed * 10)  # Simples: 10 XP por segundo de treino
    
    # 6. Adiciona ao histórico (subjetivação/evolução)
    ag.historico.append({
        "timestamp": time.time(),
        "duration": elapsed,
        "map": map_type,
        "xp_gained": xp_gained,
        "tipo_evento": "treino"
    })
    
    # 7. Limita histórico para não ficar pesado (últimas 50 ocorrências)
    ag.historico = ag.historico[-50:]
    
    # 8. Salva no JSON (persistência)
    ag_dict.update(ag.to_dict())
    agents[idx] = ag_dict
    save_agents(agents)
    
    # 9. Salva o modelo (o Agent.train() já salva checkpoints, mas força final)
    agent.save(model_path_base)
    
    print(f"[TREINO] ✓ {ag.nome} treinado por {elapsed:.1f}s no mapa {map_type}. XP ganho: {xp_gained}")
    play_sound("finish")

def criar_novo_agente(agents, interface):
    def on_submit(data):
        nome = data["nome"]
        tipo = data["tipo"]
        try:
            if any(a["nome"]==nome for a in agents):
                interface.show_message("Já existe agente com esse nome!", success=False)
                return
            ag = AgentInfo(nome, tipo)
            agents.append(ag.to_dict())
            save_agents(agents)
            play_sound("clique")
            interface.show_message("Agente criado com sucesso!", success=True)
        except Exception as e:
            interface.show_message(f"Erro ao criar agente: {e}", success=False)
    interface.show_agent_form(on_submit)

def editar_agente(ag, interface):
    def on_submit(data):
        try:
            novo_nome = data["nome"]
            novo_tipo = data["tipo"]
            ag["nome"] = novo_nome
            ag["tipo"] = novo_tipo
            agents = load_agents()
            for a in agents:
                if a["nome"]==ag["nome"]:
                    a.update(ag)
            save_agents(agents)
            play_sound("clique")
            interface.show_message("Agente editado com sucesso!", success=True)
        except Exception as e:
            interface.show_message(f"Erro ao editar agente: {e}", success=False)
    interface.show_agent_form(on_submit, agent_data=ag)

def excluir_agente(ag):
    agents = load_agents()
    agents = [a for a in agents if a["nome"]!=ag["nome"]]
    save_agents(agents)
    try:
        if ag["modelo_path"] and os.path.exists(ag["modelo_path"]):
            os.remove(ag["modelo_path"])
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
