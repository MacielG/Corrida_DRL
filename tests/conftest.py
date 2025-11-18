import pytest
import pygame
from interface_dpg import InterfaceDPG

@pytest.fixture
def interface():
    pygame.init()
    interface = InterfaceDPG(width=800, height=600, fase_desc="Test", n_parallel=2)
    yield interface
    interface.close()
