# interface_utils.py
import pygame
import gc

def clear_screen(screen, sim_width, dash_width, height):
    screen.fill((255, 255, 255))
    pygame.draw.rect(screen, (255,255,255), (0, 0, sim_width, height))
    pygame.draw.rect(screen, (245,245,245), (sim_width, 0, dash_width, height))

def update_screen():
    pygame.display.flip()

def close_interface():
    pygame.quit()
    gc.collect()
