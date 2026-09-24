"""Pixelização do sinal, compartilhada pelas câmeras e pelo susto.

Reduz a cena já composta e amplia sem interpolação. Os arquivos de arte
permanecem intactos, e a interface é desenhada depois do efeito.
"""
import pygame


class Pixelation:
    def __init__(self, scale=1.0):
        self.scale = scale
        self._small = None
        self._buffer_key = None

    def apply(self, surface, rect=None):
        """Aplica no próprio retângulo; reaproveita o buffer entre frames."""
        if self.scale >= 1.0:
            return
        rect = surface.get_rect() if rect is None else pygame.Rect(rect)
        if rect.width <= 0 or rect.height <= 0:
            return
        size = (max(1, round(rect.width * self.scale)),
                max(1, round(rect.height * self.scale)))
        source = surface.subsurface(rect)
        key = (size, source.get_bitsize(), source.get_masks())
        if key != self._buffer_key:
            self._small = pygame.Surface(size, 0, source)
            self._buffer_key = key
        # A média na redução evita ruído de amostragem em texturas finas.
        # A ampliação SEM filtro preserva os blocos do sinal reduzido.
        pygame.transform.smoothscale(source, size, self._small)
        pygame.transform.scale(self._small, rect.size, source)
