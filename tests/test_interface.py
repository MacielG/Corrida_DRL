import pytest
import pygame
from interface import Interface
from environment import CorridaEnv
from unittest.mock import Mock

@pytest.fixture
def interface():
    pygame.init()
    interface = Interface(width=800, height=600, fase_desc="Test", n_parallel=2)
    yield interface
    interface.close()

def test_draw_corridor(interface):
    corridor_rect = (100, 200, 600, 200)
    interface.draw_corridor(corridor_rect)
    assert interface.screen.get_at((150, 250)) != (255, 255, 255, 255)

def test_draw_barriers(interface):
    barriers = [(100, 100, 50, 50)]
    interface.draw_barriers(barriers)
    assert interface.screen.get_at((110, 110)) == (100, 100, 100, 255)

def test_draw_checkpoints_pulse(interface):
    checkpoints = [(400, 300)]
    interface.draw_checkpoints(checkpoints, success_idx=0)
    assert interface.screen.get_at((400, 300)) != (255, 255, 255, 255)

def test_draw_car_trajectory(interface):
    pos = [400, 300]
    angle = 0
    traj = [(390, 300), (395, 300), (400, 300)]
    interface.draw_car(pos, angle, traj=traj)
    assert interface.screen.get_at((395, 300)) != (255, 255, 255, 255)

def test_process_events_pause(interface, monkeypatch):
    monkeypatch.setattr(pygame, "mouse", Mock(get_pos=lambda: (interface.buttons["pause"].x + 10, interface.buttons["pause"].y + 10)))
    monkeypatch.setattr(pygame, "event", Mock(get=lambda: [Mock(type=pygame.MOUSEBUTTONDOWN)]))
    interface.process_events()
    assert interface.paused is True

def test_process_events_map_menu(interface, monkeypatch):
    # Simula clique no botão "Mudar Mapa"
    monkeypatch.setattr(pygame, "mouse", Mock(get_pos=lambda: (interface.buttons["map"].x + 10, interface.buttons["map"].y + 10)))
    monkeypatch.setattr(pygame, "event", Mock(get=lambda: [Mock(type=pygame.MOUSEBUTTONDOWN)]))
    interface.process_events()
    assert interface.menu_active is True
    # Simula clique na opção "corridor" (primeira opção do menu)
    menu_y = interface.buttons["map"].y + 50  # y do menu + 0*50
    monkeypatch.setattr(pygame, "mouse", Mock(get_pos=lambda: (interface.sim_width + 30, menu_y + 10)))
    interface.process_events()
    assert interface.selected_map == "corridor"
    assert interface.menu_active is False

def test_draw_dashboard_empty(interface):
    interface.draw_dashboard([], [], [], 0, 0.0, 0)
    assert interface.screen.get_at((interface.sim_width + 20, 50)) != (255, 255, 255, 255)

def test_draw_multi_agents(interface):
    env = CorridaEnv(map_type="corridor")
    states = [[400, 300, 1, 0, 1, 0, 0] * 2]
    interface.draw_multi_agents(env, states=states)
    assert interface.screen.get_at((400, 300)) != (255, 255, 255, 255)
