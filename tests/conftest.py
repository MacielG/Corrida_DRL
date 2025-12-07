import pytest
import pygame
import json
import os
import tempfile
from interface_dpg import InterfaceDPG

@pytest.fixture
def interface():
    pygame.init()
    interface = InterfaceDPG(width=800, height=600, fase_desc="Test", n_parallel=2)
    yield interface
    interface.close()

@pytest.fixture
def temp_agents_file(tmp_path):
    """Fixture que cria arquivo temporário de agentes para testes"""
    agents_data = [
        {
            "id": 1,
            "nome": "Agente Test 1",
            "algoritmo": "DQN",
            "pontos": 100,
            "level": 1,
            "xp": 50,
            "vitórias": 0,
            "derrotas": 0
        },
        {
            "id": 2,
            "nome": "Agente Test 2",
            "algoritmo": "PPO",
            "pontos": 200,
            "level": 2,
            "xp": 150,
            "vitórias": 1,
            "derrotas": 0
        }
    ]
    
    agents_file = tmp_path / "agents_test.json"
    with open(agents_file, 'w') as f:
        json.dump(agents_data, f)
    
    yield str(agents_file)
    
    # Cleanup
    if agents_file.exists():
        agents_file.unlink()
