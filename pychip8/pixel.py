import contextlib

with contextlib.redirect_stdout(None):
    import pygame

class Pixel(pygame.sprite.Sprite):
    def __init__(self, width, color):
        self.surf = pygame.Surface((width, width))
        self.surf.fill(color)
        self.rect = self.surf.get_rect()
