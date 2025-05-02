import pytest
import pygame
from interface import Interface

@pytest.fixture
def interface():
    pygame.init()
    interface = Interface(width=800, height=600, fase_desc="Test", n_parallel=2)
    yield interface
    interface.close()
