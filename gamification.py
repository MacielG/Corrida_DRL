"""Sistema de Gamificação para Corrida DRL.

Implementa:
- Sistema de níveis baseado em XP
- Upgrades de stats de carros (aceleração, velocidade, controle)
- Desbloqueio de mapas por nível
- Achievements
"""

import math
from interface_agents import AgentInfo, load_agents, save_agents

class GamificationSystem:
    """Sistema completo de gamificação para agentes RL."""
    
    # Configuração de mapas bloqueados por nível
    MAP_UNLOCK_LEVELS = {
        "corridor": 1,      # Disponível desde o início
        "curve": 5,         # Desbloqueado no nível 5
        "circle": 10        # Desbloqueado no nível 10
    }
    
    # Configuração de upgrades disponíveis por nível
    UPGRADES = {
        "accel": {
            "nome": "Melhor Motor",
            "custo_xp": 100,
            "incremento": 0.05,
            "maximo": 1.0,
            "descricao": "Aumenta a aceleração do carro"
        },
        "turn_speed": {
            "nome": "Direção Ajustada",
            "custo_xp": 80,
            "incremento": 0.5,
            "maximo": 15.0,
            "descricao": "Melhora a velocidade de virada"
        },
        "max_speed": {
            "nome": "Turbo",
            "custo_xp": 150,
            "incremento": 1.0,
            "maximo": 30.0,
            "descricao": "Aumenta a velocidade máxima"
        }
    }
    
    @staticmethod
    def calculate_level(total_xp):
        """Calcula nível a partir de XP total.
        
        Usa fórmula exponencial: Nível = floor(sqrt(XP/100)) + 1
        """
        return max(1, int(math.sqrt(total_xp / 100)) + 1)
    
    @staticmethod
    def calculate_next_level_xp(current_level):
        """Calcula XP necessário para o próximo nível."""
        return (current_level ** 2) * 100
    
    @staticmethod
    def calculate_xp_progress(total_xp):
        """Calcula progresso para o próximo nível (0.0 a 1.0)."""
        current_level = GamificationSystem.calculate_level(total_xp)
        current_level_xp = ((current_level - 1) ** 2) * 100
        next_level_xp = (current_level ** 2) * 100
        
        if next_level_xp == current_level_xp:
            return 0.0
        
        progress = (total_xp - current_level_xp) / (next_level_xp - current_level_xp)
        return min(1.0, max(0.0, progress))
    
    @staticmethod
    def is_map_unlocked(map_name, agent_level):
        """Verifica se um mapa está desbloqueado para o agente."""
        required_level = GamificationSystem.MAP_UNLOCK_LEVELS.get(map_name, 1)
        return agent_level >= required_level
    
    @staticmethod
    def get_available_maps(agent_level):
        """Retorna lista de mapas disponíveis para o nível do agente."""
        return [
            map_name for map_name, required_level in GamificationSystem.MAP_UNLOCK_LEVELS.items()
            if agent_level >= required_level
        ]
    
    @staticmethod
    def can_upgrade(agent_info, upgrade_name):
        """Verifica se um agente pode fazer um upgrade específico."""
        if upgrade_name not in GamificationSystem.UPGRADES:
            return False, "Upgrade não encontrado"
        
        upgrade_config = GamificationSystem.UPGRADES[upgrade_name]
        total_xp = sum(h.get('xp_gained', 0) for h in agent_info.historico)
        
        # Verifica XP
        if total_xp < upgrade_config["custo_xp"]:
            return False, f"Faltam {upgrade_config['custo_xp'] - total_xp} XP"
        
        # Verifica se já está no máximo
        current_value = agent_info.stats[upgrade_name]
        if current_value >= upgrade_config["maximo"]:
            return False, f"Já está no máximo ({upgrade_config['maximo']})"
        
        return True, "Pode fazer upgrade"
    
    @staticmethod
    def apply_upgrade(agent_info, upgrade_name):
        """Aplica um upgrade a um agente.
        
        Returns:
            tuple: (sucesso, mensagem)
        """
        can_upgrade, msg = GamificationSystem.can_upgrade(agent_info, upgrade_name)
        if not can_upgrade:
            return False, msg
        
        upgrade_config = GamificationSystem.UPGRADES[upgrade_name]
        
        # Incrementa o stat
        agent_info.stats[upgrade_name] = min(
            agent_info.stats[upgrade_name] + upgrade_config["incremento"],
            upgrade_config["maximo"]
        )
        
        # Incrementa nível
        agent_info.level += 1
        
        return True, f"Upgrade '{upgrade_config['nome']}' aplicado!"
    
    @staticmethod
    def get_upgrades_available(agent_info):
        """Retorna lista de upgrades que o agente pode fazer."""
        upgrades = []
        for upgrade_name, config in GamificationSystem.UPGRADES.items():
            can_upgrade, msg = GamificationSystem.can_upgrade(agent_info, upgrade_name)
            upgrades.append({
                "id": upgrade_name,
                "nome": config["nome"],
                "descricao": config["descricao"],
                "custo_xp": config["custo_xp"],
                "disponivel": can_upgrade
            })
        return upgrades
    
    @staticmethod
    def update_agent_stats(agent_name):
        """Atualiza stats calculados de um agente após uma sessão de treino.
        
        Isso é chamado ao final de cada corrida/treino.
        """
        agents = [AgentInfo.from_dict(a) for a in load_agents()]
        agent = next((a for a in agents if a.nome == agent_name), None)
        
        if not agent:
            return None
        
        # Calcula XP total
        total_xp = sum(h.get('xp_gained', 0) for h in agent.historico)
        agent.level = GamificationSystem.calculate_level(total_xp)
        
        # Salva atualização
        agents_dicts = [a.to_dict() for a in agents]
        agent_dict = next((a for a in agents_dicts if a["nome"] == agent_name), None)
        if agent_dict:
            agent_dict["level"] = agent.level
            save_agents(agents_dicts)
        
        return agent

class Achievement:
    """Representa um achievement desbloqueável no jogo."""
    
    ACHIEVEMENTS = {
        "primeiro_checkpoint": {
            "nome": "Primeiro Passo",
            "descricao": "Completar o primeiro checkpoint",
            "icon": "🚩"
        },
        "perfeito_corridor": {
            "nome": "Corredeiro Perfeito",
            "descricao": "Completar corridor com zero colisões",
            "icon": "✨"
        },
        "speedrun": {
            "nome": "Rápido Demais",
            "descricao": "Completar corrida em menos de 10 segundos",
            "icon": "⚡"
        },
        "nivel_10": {
            "nome": "Piloto Experiente",
            "descricao": "Atingir nível 10",
            "icon": "🏆"
        },
        "upgrade_completo": {
            "nome": "Totalmente Aprimorado",
            "descricao": "Maxar todos os upgrades de um carro",
            "icon": "🔧"
        }
    }
    
    @staticmethod
    def check_achievement(agent_info, achievement_id):
        """Verifica se um agente desbloqueou um achievement."""
        if achievement_id not in Achievement.ACHIEVEMENTS:
            return False
        
        total_xp = sum(h.get('xp_gained', 0) for h in agent_info.historico)
        
        if achievement_id == "primeiro_checkpoint":
            return any(h.get("checkpoints", 0) > 0 for h in agent_info.historico)
        elif achievement_id == "perfeito_corridor":
            return any(h.get("checkpoints", 0) >= 1 and h.get("mapa") == "corridor" for h in agent_info.historico)
        elif achievement_id == "speedrun":
            return any(h.get("tempo", float('inf')) < 10 for h in agent_info.historico)
        elif achievement_id == "nivel_10":
            return agent_info.level >= 10
        elif achievement_id == "upgrade_completo":
            return (agent_info.stats["accel"] >= 1.0 and 
                    agent_info.stats["turn_speed"] >= 15.0 and 
                    agent_info.stats["max_speed"] >= 30.0)
        
        return False
    
    @staticmethod
    def get_unlocked_achievements(agent_info):
        """Retorna lista de achievements desbloqueados."""
        unlocked = []
        for achievement_id in Achievement.ACHIEVEMENTS:
            if Achievement.check_achievement(agent_info, achievement_id):
                achievement = Achievement.ACHIEVEMENTS[achievement_id].copy()
                achievement["id"] = achievement_id
                unlocked.append(achievement)
        return unlocked
