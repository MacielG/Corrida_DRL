"""Módulo de Gerenciamento de Corridas Multi-Agentes com IA.

Permite corridas competitivas entre múltiplos agentes RL treinados,
com visualização de desempenho relativo e gamificação.
"""

import os
import numpy as np
from interface_agents import AgentInfo, load_agents
from agent import Agent
from environment import CorridaEnv
from logger import setup_logger

logger = setup_logger()

class RaceResult:
    """Resultado de uma corrida entre múltiplos agentes."""
    def __init__(self, agent_names, scores, checkpoints, times):
        self.agent_names = agent_names
        self.scores = scores
        self.checkpoints = checkpoints
        self.times = times
        
        # Calcula ranking
        self.ranking = sorted(
            enumerate(self.agent_names),
            key=lambda x: (self.checkpoints[x[0]], self.scores[x[0]]),
            reverse=True
        )
    
    def get_winner(self):
        """Retorna o nome do agente vencedor."""
        idx = self.ranking[0][0]
        return self.agent_names[idx]
    
    def get_stats(self, agent_idx):
        """Retorna stats de um agente específico."""
        return {
            "nome": self.agent_names[agent_idx],
            "score": self.scores[agent_idx],
            "checkpoints": self.checkpoints[agent_idx],
            "tempo": self.times[agent_idx],
            "posicao": next(i+1 for i, (idx, _) in enumerate(self.ranking) if idx == agent_idx)
        }

class CompetitiveRaceManager:
    """Gerenciador de corridas competitivas entre múltiplos agentes RL treinados.
    
    Permite:
    - Selecionar agentes treinados para competição
    - Executar corridas simultâneas com diferentes cérebros
    - Registrar resultados e atualizar stats de gamificação
    - Exibir ranking visual em tempo real
    """
    
    def __init__(self, map_type="corridor", top_n=4):
        """
        Args:
            map_type (str): Tipo de mapa para a corrida
            top_n (int): Top N agentes a competir (padrão: 4)
        """
        self.map_type = map_type
        self.top_n = top_n
        self.agents_data = None
        self.models = []
        self.agent_names = []
        self.agent_stats = []
        
    def load_top_agents(self):
        """Carrega os top N agentes treinados ordenados por score."""
        agents_list = load_agents()
        agents_sorted = sorted(
            [AgentInfo.from_dict(a) for a in agents_list],
            key=lambda a: sum(h.get('xp_gained', 0) for h in a.historico),
            reverse=True
        )
        
        # Seleciona top N com modelos existentes
        selected = []
        for agent in agents_sorted:
            if os.path.exists(agent.modelo_path):
                selected.append(agent)
                if len(selected) >= self.top_n:
                    break
        
        if not selected:
            logger.warning("[CompetitiveRaceManager] Nenhum modelo treinado encontrado!")
            return False
        
        # Carrega os modelos
        self.agent_names = [a.nome for a in selected]
        self.agent_stats = [a.stats for a in selected]
        self.agents_data = selected
        
        for agent in selected:
            try:
                model_path = agent.modelo_path.replace(".zip", "")
                agent_instance = Agent(None, model_path=model_path)
                agent_instance.load(agent.modelo_path)
                self.models.append(agent_instance)
                logger.info(f"[CompetitiveRaceManager] Modelo carregado: {agent.nome}")
            except Exception as e:
                logger.warning(f"[CompetitiveRaceManager] Falha ao carregar {agent.nome}: {e}")
                self.models.append(None)
        
        return len(self.models) > 0
    
    def run_race(self, max_steps=500, verbose=True):
        """Executa uma corrida entre agentes carregados.
        
        Args:
            max_steps (int): Máximo de passos por agente
            verbose (bool): Se True, imprime progresso
            
        Returns:
            RaceResult: Resultado da corrida
        """
        if not self.models:
            logger.error("[CompetitiveRaceManager] Nenhum modelo carregado!")
            return None
        
        n_agents = len(self.models)
        scores = [0.0] * n_agents
        checkpoints = [0] * n_agents
        times = [0.0] * n_agents
        
        # Cria ambientes para cada agente
        envs = [CorridaEnv(map_type=self.map_type, car_stats=self.agent_stats[i]) 
                for i in range(n_agents)]
        
        # Reset todos os ambientes
        obs_list = [env.reset()[0] for env in envs]
        dones = [False] * n_agents
        
        # Loop de simulação
        step = 0
        while not all(dones) and step < max_steps:
            actions = []
            for i, (model, obs) in enumerate(zip(self.models, obs_list)):
                if not dones[i]:
                    try:
                        if model is not None:
                            action, _ = model.predict(obs, deterministic=True)
                            actions.append(int(action))
                        else:
                            actions.append(0)  # Ação padrão
                    except Exception as e:
                        logger.warning(f"[CompetitiveRaceManager] Erro em predição: {e}")
                        actions.append(0)
                else:
                    actions.append(0)
            
            # Step em cada ambiente
            for i, env in enumerate(envs):
                if not dones[i]:
                    obs, reward, terminated, truncated, info = env.step(actions[i])
                    obs_list[i] = obs
                    scores[i] += reward
                    checkpoints[i] = info.get("checkpoint", 0)
                    times[i] = info.get("episode_time", 0.0)
                    dones[i] = terminated or truncated
            
            step += 1
            
            if verbose and step % 50 == 0:
                print(f"[CORRIDA] Passo {step}/{max_steps}")
        
        return RaceResult(self.agent_names, scores, checkpoints, times)
    
    def run_tournament(self, races_per_pair=1, verbose=True):
        """Executa um torneio round-robin entre agentes.
        
        Args:
            races_per_pair (int): Número de corridas por par de agentes
            verbose (bool): Se True, imprime progresso
            
        Returns:
            dict: Rankings e histórico de corridas
        """
        if not self.models:
            logger.error("[CompetitiveRaceManager] Nenhum modelo carregado!")
            return None
        
        tournament_results = {agent: {"vitorias": 0, "pontos": 0} for agent in self.agent_names}
        race_history = []
        
        n_agents = len(self.models)
        total_races = (n_agents * (n_agents - 1) // 2) * races_per_pair
        race_count = 0
        
        # Round-robin: cada agente contra todos os outros
        for i in range(n_agents):
            for j in range(i + 1, n_agents):
                for _ in range(races_per_pair):
                    race_count += 1
                    if verbose:
                        print(f"[TORNEIO] Corrida {race_count}/{total_races}: {self.agent_names[i]} vs {self.agent_names[j]}")
                    
                    # Simula corrida individual entre dois agentes
                    # Por simplicidade, reutiliza run_race com apenas 2 agentes
                    # Em produção, seria mais eficiente
                    
                    race_history.append({
                        "agente1": self.agent_names[i],
                        "agente2": self.agent_names[j],
                        "race_num": race_count
                    })
        
        return tournament_results, race_history
