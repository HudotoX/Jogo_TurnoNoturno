"""Ponto de entrada com renderização lógica e janela adaptável.

O jogo continua desenhando em 1920x1080 internamente, mas a imagem é
reduzida com letterbox para caber no monitor/projetor disponível. Assim o
layout não é cortado em telas de 1366x768 ou 1280x720.
"""

import sys

import pygame

import settings as cfg
from game import Game


LOGICAL_SIZE = (cfg.WIDTH, cfg.HEIGHT)


def _fit_window(desktop_size):
    """Maior janela 16:9 que cabe na área de trabalho."""
    dw, dh = desktop_size
    margin = 40
    available_w = max(640, dw - margin)
    available_h = max(360, dh - margin)
    scale = min(1.0, available_w / cfg.WIDTH, available_h / cfg.HEIGHT)
    return max(640, int(cfg.WIDTH * scale)), max(360, int(cfg.HEIGHT * scale))


def _viewport(window_size):
    """Retângulo 16:9 centralizado dentro da janela atual."""
    ww, wh = window_size
    scale = min(ww / cfg.WIDTH, wh / cfg.HEIGHT)
    width = max(1, int(cfg.WIDTH * scale))
    height = max(1, int(cfg.HEIGHT * scale))
    return pygame.Rect((ww - width) // 2, (wh - height) // 2, width, height)


def _logical_mouse_event(event, view):
    """Converte coordenadas do mouse da janela para o canvas 1920x1080."""
    if not hasattr(event, "pos"):
        return event
    if not view.collidepoint(event.pos):
        data = dict(event.dict)
        data["pos"] = (-1, -1)
        return pygame.event.Event(event.type, data)
    lx = int((event.pos[0] - view.x) * cfg.WIDTH / view.width)
    ly = int((event.pos[1] - view.y) * cfg.HEIGHT / view.height)
    data = dict(event.dict)
    data["pos"] = (lx, ly)
    return pygame.event.Event(event.type, data)


def main():
    pygame.init()
    desktop = pygame.display.get_desktop_sizes()[0]
    windowed_size = _fit_window(desktop)
    flags = pygame.RESIZABLE
    screen = pygame.display.set_mode(windowed_size, flags)
    pygame.display.set_caption(cfg.TITLE)
    logical = pygame.Surface(LOGICAL_SIZE).convert()
    clock = pygame.time.Clock()
    game = Game(logical)
    fullscreen = False

    running = True
    while running:
        dt = min(clock.tick(cfg.FPS) / 1000.0, 0.1)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                game.fullscreen_requested = True
            elif event.type == pygame.VIDEORESIZE and not fullscreen:
                game.release_mouse_hold()
                windowed_size = (max(640, event.w), max(360, event.h))
                screen = pygame.display.set_mode(windowed_size, flags)
            else:
                # A janela pode ter mudado dentro do mesmo lote de eventos.
                game.handle_event(_logical_mouse_event(event, _viewport(screen.get_size())))

        if game.fullscreen_requested:
            game.fullscreen_requested = False
            game.release_mouse_hold()
            fullscreen = not fullscreen
            if fullscreen:
                screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                screen = pygame.display.set_mode(windowed_size, flags)
            game.ui.fullscreen = fullscreen

        game.update(dt)
        game.draw()

        screen.fill((0, 0, 0))
        view = _viewport(screen.get_size())
        if view.size == LOGICAL_SIZE:
            scaled = logical
        else:
            scaled = pygame.transform.smoothscale(logical, view.size)
        screen.blit(scaled, view.topleft)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
