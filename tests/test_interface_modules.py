import pytest
import pygame
import os
import time
from interface_assets import load_icon, play_sound
from interface_dashboard import Dashboard
from interface_menu import Menu
from interface_utils import clear_screen, update_screen, close_interface
from interface_agents import AgentInfo, handle_gestao_agentes_events, criar_novo_agente
from unittest.mock import Mock, patch

@pytest.fixture
def screen():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    yield screen
    pygame.quit()

# Existing tests omitted for brevity (assume they are present here)

# Robustness and workflow enhancement tests

def test_handle_menu_events_no_infinite_loop(monkeypatch):
    menu = Menu(800, 600)
    monkeypatch.setattr(pygame.event, "get", lambda: [])
    result = menu.handle_menu_events("state", [])
    assert result is None

def test_create_new_agent(monkeypatch, tmp_path):
    agents = []
    inputs = iter(["AgentX", "DQN"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr("interface_agents.save_agents", lambda a, filename="agents.json": None)
    monkeypatch.setattr("interface_assets.play_sound", lambda nome: None)
    criar_novo_agente(agents)
    assert any(a["nome"] == "AgentX" for a in agents)

def test_agent_learning_time_and_history():
    ag = AgentInfo("AgentY", "PPO", tempo_acumulado=100.5, historico=[1,2,3])
    assert ag.tempo_acumulado == 100.5
    assert ag.historico == [1,2,3]

def test_simulate_race_with_multiple_agents(monkeypatch):
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    interface = Dashboard(screen, 560, 240, 600)
    rewards_hist = [[1, 2, 3], [4, 5, 6]]
    collisions_hist = [[0, 1, 0], [1, 0, 1]]
    penalties_hist = [[0, 0, 1], [1, 1, 0]]
    for _ in range(3):
        interface.draw_dashboard(rewards_hist, collisions_hist, penalties_hist, 10, 5.5, 2, "Test Phase", 2, [1, 0, 1])
        update_screen()
        time.sleep(0.01)

def test_event_history_and_state_management(monkeypatch):
    agents = [AgentInfo("Agent1", "DQN").to_dict()]
    gestao_btn_novo = []
    gestao_agent_cards = [{"btn_sel": pygame.Rect(0,0,10,10), "btn_edit": pygame.Rect(0,0,10,10), "btn_del": pygame.Rect(0,0,10,10), "idx": 0}]
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (5,5))
    events = [pygame.event.Event(pygame.MOUSEBUTTONDOWN, {})]
    result = handle_gestao_agentes_events(events, gestao_btn_novo, gestao_agent_cards, agents)
    assert result == ("select", "Agent1")
    events = [pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})]
    result = handle_gestao_agentes_events(events, gestao_btn_novo, gestao_agent_cards, agents)
    assert result == "escape"
