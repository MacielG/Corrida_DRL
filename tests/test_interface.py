import pytest
import pygame
import os
from interface_dpg import InterfaceDPG
from environment import CorridaEnv
from interface_select import SelectScreen
from interface_ranking import RankingScreen
from interface_agents import AgentInfo, handle_gestao_agentes_events
from unittest.mock import Mock

@pytest.fixture
def interface():
    pygame.init()
    interface = InterfaceDPG(width=800, height=600, fase_desc="Test", n_parallel=2)
    yield interface
    interface.close()

def test_draw_corridor(interface):
    corridor_rect = (100, 200, 600, 200)
    interface.draw_corridor(corridor_rect)
    assert interface.screen.get_at((105, 205))[:3] == (0, 0, 0)

def test_draw_barriers(interface):
    barriers = [(100, 100, 50, 50)]
    interface.draw_barriers(barriers)
    assert interface.screen.get_at((110, 110))[:3] == (100, 100, 100)

def test_draw_checkpoints_pulse(interface):
    checkpoints = [(400, 300)]
    interface.draw_checkpoints(checkpoints, success_idx=0)
    color = interface.screen.get_at((400, 300))
    assert color.g > 0

def test_draw_car_trajectory(interface):
    pos = [400, 300]
    angle = 0
    traj = [(390, 300), (395, 300), (400, 300)]
    interface.draw_car(pos, angle, traj=traj)
    color = interface.screen.get_at((395, 300))
    assert color.r > 0

def test_toggle_pause(interface):
    # CORREÇÃO: Teste simples de toggle_pause
    initial = interface.paused
    interface.toggle_pause()
    assert interface.paused == (not initial)

def test_request_restart(interface):
    # CORREÇÃO: Teste de restart
    assert not interface.should_restart()
    interface.request_restart()
    assert interface.should_restart()
    interface.clear_restart()
    assert not interface.should_restart()

def test_draw_dashboard_empty(interface):
    # CORREÇÃO: Passou argumentos corretos para draw_dashboard
    interface.draw_dashboard([], [], [], 0, 0.0, 0)
    assert interface.screen.get_at((interface.sim_width + 20, 50))[:3] != (255, 255, 255)

def test_draw_env_grid_simple(interface):
    # CORREÇÃO: Testa draw_env_grid_simple ao invés de draw_multi_agents (não existe)
    env = CorridaEnv(map_type="corridor")
    env.reset()
    interface.draw_env_grid_simple(env, 0)
    # Verifica que algo foi desenhado na grade
    assert interface.screen.get_at((50, 50))[:3] != (255, 255, 255)

# Additional tests for agent selection, ranking, events, names, and models

def test_select_screen_agent_selection(monkeypatch):
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    select_screen = SelectScreen(800, 600)
    select_screen.draw_selecao_agente(screen, selected_agent="DQN", selected_map="corridor")
    assert len(select_screen.agente_btns) == 3
    found = any(ag == "DQN" for ag, rect in select_screen.agente_btns)
    assert found

def test_ranking_screen_instantiation():
    ranking_screen = RankingScreen(800, 600)
    assert ranking_screen.width == 800
    assert ranking_screen.height == 600

def test_agent_info_serialization(tmp_path):
    ag = AgentInfo("TestAgent", "DQN", tempo_acumulado=12.3)
    d = ag.to_dict()
    ag2 = AgentInfo.from_dict(d)
    assert ag.nome == ag2.nome
    assert ag.tipo == ag2.tipo
    assert ag.tempo_acumulado == ag2.tempo_acumulado
    assert ag.modelo_path == ag2.modelo_path

def test_handle_gestao_agentes_events_select(monkeypatch):
    pygame.init()
    agents = [AgentInfo("Agent1", "DQN").to_dict(), AgentInfo("Agent2", "PPO").to_dict()]
    gestao_btn_novo = []
    gestao_agent_cards = [{"btn_sel": pygame.Rect(0,0,10,10), "btn_edit": pygame.Rect(0,0,10,10), "btn_del": pygame.Rect(0,0,10,10), "idx": 0}]
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (5,5))
    events = [pygame.event.Event(pygame.MOUSEBUTTONDOWN, {})]
    result = handle_gestao_agentes_events(events, gestao_btn_novo, gestao_agent_cards, agents)
    assert result == ("select", "Agent1")
