# interface_assets.py
import pygame
import os

def load_icon(path, fallback_color=(200,200,200), size=(64,64)):
    try:
        img = pygame.image.load(path)
        return pygame.transform.smoothscale(img, size)
    except Exception:
        surf = pygame.Surface(size)
        surf.fill(fallback_color)
        return surf

def play_sound(nome):
    try:
        pygame.mixer.init()
        sound = pygame.mixer.Sound(f'assets/{nome}.wav')
        sound.play()
    except Exception:
        pass
