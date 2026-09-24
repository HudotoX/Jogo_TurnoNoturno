"""
ui.py
Todo o desenho de interface que não é o feed de câmera em si:
HUD (relógio, estabilidade, prompts), telas de menu, intro de noite,
tela de game over e tela de vitória.

O visual geral (fora do feed de câmera em si, que mantém seu estilo de
"filmagem" em camera_system.py) imita uma área de trabalho de um PC
antigo, estilo janelas 3D com relevo: `draw_bevel_rect` desenha esse
relevo, `draw_window_chrome` monta uma "janela" completa (barra de
título azul, botão de fechar, corpo cinza) em cima disso.

Suporte a asset real: se existir uma fonte em
  assets/fonts/main.ttf
ela é usada em todo o jogo no lugar da fonte padrão do sistema — sem
precisar mudar nada aqui, só colocar o arquivo com esse nome na pasta.
"""

import os
import datetime
import pygame
import settings as cfg
from care_ui import CareUI
from story_ui import StoryUI
from video_effects import Pixelation

FONTS_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")
SPRITES_DIR = os.path.join(os.path.dirname(__file__), "assets", "sprites")
CUSTOM_FONT_PATH = os.path.join(FONTS_DIR, "main.ttf")
JUMPSCARE_SPRITE_PATH = os.path.join(SPRITES_DIR, "jumpscare.png")


def load_font(size, bold=False):
    """Carrega a fonte customizada se existir; senão cai na fonte do sistema."""
    if os.path.isfile(CUSTOM_FONT_PATH):
        try:
            return pygame.font.Font(CUSTOM_FONT_PATH, size)
        except pygame.error:
            pass
    return pygame.font.SysFont(cfg.FONT_NAME, size, bold=bold)


class UI(CareUI, StoryUI):
    def __init__(self):
        self.pixelation = Pixelation(cfg.PIXEL_SCALE)
        self.fullscreen = False
        self.font_small = load_font(16)
        self.font_medium = load_font(22, bold=True)
        self.font_large = load_font(40, bold=True)
        self.font_title = load_font(58, bold=True)
        self.font_care = load_font(25)
        self.font_care_bold = load_font(25, bold=True)
        self.font_story = load_font(29)
        self.font_story_small = load_font(26)
        self._t = 0.0

        self._jumpscare_sprite = None
        self._scare_frames = []
        if os.path.isfile(JUMPSCARE_SPRITE_PATH):
            try:
                self._jumpscare_sprite = pygame.image.load(JUMPSCARE_SPRITE_PATH).convert()
                self._prepare_scare_frames()
            except pygame.error:
                self._jumpscare_sprite = None

        # ---------- texto de abertura da noite (efeito de máquina de
        # escrever, revela a lore aos poucos) ----------
        self._lore_text = ""
        self._lore_reveal_chars = 0.0
        self._lore_full = True

    def start_night_lore(self, text):
        """Chamado por game.py ao entrar na tela de intro da noite —
        começa a 'digitar' o texto de lore do zero."""
        self._lore_text = text or ""
        self._lore_reveal_chars = 0.0
        self._lore_full = not bool(text)

    def skip_lore(self):
        """Revela o texto inteiro na hora (jogador pediu pra pular)."""
        self._lore_reveal_chars = len(self._lore_text)
        self._lore_full = True

    def lore_fully_revealed(self):
        return self._lore_full

    def tick(self, dt):
        self._t += dt
        if not self._lore_full and self._lore_text:
            self._lore_reveal_chars += dt / cfg.LORE_CHAR_SECONDS
            if self._lore_reveal_chars >= len(self._lore_text):
                self._lore_reveal_chars = len(self._lore_text)
                self._lore_full = True

    # ------------------------------------------------------------------
    def game_clock_string(self, night_elapsed_seconds):
        progress = min(1.0, night_elapsed_seconds / cfg.NIGHT_DURATION_SECONDS)
        total_minutes_ingame = progress * (cfg.NIGHT_END_HOUR - cfg.NIGHT_START_HOUR) * 60
        hour = cfg.NIGHT_START_HOUR + int(total_minutes_ingame // 60)
        minute = int(total_minutes_ingame % 60)
        return f"{hour:02d}:{minute:02d}"

    # ------------------------------------------------------------------
    def draw_vertical_gradient(self, surface, rect, top_color, bottom_color):
        steps = max(1, rect.height // 3)
        for i in range(steps):
            t = i / steps
            color = tuple(int(top_color[k] + (bottom_color[k] - top_color[k]) * t) for k in range(3))
            y = rect.top + int(rect.height * t)
            h = rect.height // steps + 1
            pygame.draw.rect(surface, color, (rect.left, y, rect.width, h))

    # ------------------------------------------------------------------
    def draw_stability_bar(self, surface, rect, label, value, state):
        # barra "afundada" estilo Windows 95 (mesmo visual de uma barra
        # de progresso clássica), com o preenchimento colorido por estado
        self.draw_bevel_rect(surface, rect, raised=False, face=cfg.WIN95_FACE_LIGHT)
        inner = rect.inflate(-4, -4)

        fill_w = max(0, int(inner.width * (value / cfg.STABILITY_MAX)))
        color = cfg.STATE_COLORS.get(state, cfg.COLOR_ACCENT)
        if fill_w > 0:
            fill_rect = pygame.Rect(inner.left, inner.top, fill_w, inner.height)
            pygame.draw.rect(surface, color, fill_rect)

        if state in ("ANORMAL", "PERIGO"):
            blink = int(self._t * 6) % 2 == 0
            if blink:
                pygame.draw.rect(surface, cfg.WIN95_DARK_SHADOW, rect, 1)

        label_surf = self.font_medium.render(f"{label}", True, cfg.WIN95_TEXT)
        state_surf = self.font_medium.render(state, True, cfg.WIN95_TEXT)
        surface.blit(label_surf, (rect.left, rect.top - 24))
        surface.blit(state_surf, (rect.right - state_surf.get_width(), rect.top - 24))
        reading = self.font_medium.render(f"{value:.0f}/100", True, cfg.WIN95_TEXT)
        surface.blit(reading, reading.get_rect(center=rect.center))

    # ------------------------------------------------------------------
    def draw_stability_bar_locked(self, surface, rect, label, patient):
        """Versão 'sem sinal' da barra — desenhada quando o paciente NÃO
        está na câmera ativa no momento. Mostra só um snapshot congelado
        (última leitura real, de quando a câmera esteve nele por último),
        hachurado, pra deixar claro que não é o valor atual. É o que dá
        peso a trocar de câmera: sem olhar, você só sabe como ele estava,
        não como está agora."""
        self.draw_bevel_rect(surface, rect, raised=False, face=cfg.WIN95_FACE_LIGHT)
        inner = rect.inflate(-4, -4)

        frac = max(0.0, patient.last_known_stability / cfg.STABILITY_MAX)
        fill_w = max(0, int(inner.width * frac))
        if fill_w > 0:
            stale = pygame.Surface((fill_w, inner.height), pygame.SRCALPHA)
            stale.fill((*cfg.WIN95_TEXT_DIM, 130))
            surface.blit(stale, inner.topleft)

        # hachura diagonal simples = "sinal não confiável agora"
        hatch = pygame.Surface((inner.width, inner.height), pygame.SRCALPHA)
        step = 11
        for x in range(-inner.height, inner.width, step):
            pygame.draw.line(hatch, (0, 0, 0, 55), (x, inner.height), (x + inner.height, 0), 2)
        surface.blit(hatch, inner.topleft)

        known_room = patient.last_known_room
        cam_index = cfg.CAMERAS.index(known_room) + 1 if known_room in cfg.CAMERAS else None
        cam_tag = f"CAM {cam_index:02d}" if cam_index else "?"
        label_surf = self.font_medium.render(f"{label}", True, cfg.WIN95_TEXT_DIM)
        loc_surf = self.font_medium.render(f"última: {cam_tag}", True, cfg.WIN95_TEXT_DIM)
        surface.blit(label_surf, (rect.left, rect.top - 24))
        surface.blit(loc_surf, (rect.right - loc_surf.get_width(), rect.top - 24))

        concerning = (patient.last_known_state in (cfg.STATE_ANORMAL, cfg.STATE_PERIGO)
                      or patient.last_known_stability <= cfg.PROTOCOL_RECOMMEND_THRESHOLD)
        if concerning:
            blink = int(self._t * 6) % 2 == 0
            warn = self.font_medium.render(
                "Leitura preocupante — verifique", True, (140, 30, 30))
            if blink:
                surface.blit(warn, (rect.left, rect.bottom + 6))
        else:
            ago_text = f"última leitura há {patient.seconds_since_seen:.0f}s"
            ago_surf = self.font_medium.render(ago_text, True, cfg.WIN95_TEXT_DIM)
            surface.blit(ago_surf, (rect.left, rect.bottom + 6))

    # ------------------------------------------------------------------
    def stability_bar_rects(self, count, panel_top):
        """Geometria das barras de estabilidade — usada tanto pra
        desenhar quanto pro clique do mouse (inicia protocolo)."""
        bar_w = 330
        x0 = 210
        return [pygame.Rect(x0 + i * (bar_w + 30), panel_top + 36, bar_w, 24) for i in range(count)]

    def patient_protocol_rects(self, count, panel_top):
        return [pygame.Rect(bar.left, bar.bottom + 34, bar.width, 30)
                for bar in self.stability_bar_rects(count, panel_top)]

    def draw_hud(self, surface, game, panel_bottom=None):
        # barra de status estilo Windows 95, fixa na base da "janela" do
        # programa (não necessariamente a base física da tela — ver
        # game.py:_draw_playing, que reserva espaço pra barra de título
        # em cima e a barra de tarefas embaixo).
        panel_bottom = cfg.HEIGHT if panel_bottom is None else panel_bottom
        panel = pygame.Rect(0, panel_bottom - 130, cfg.WIDTH, 130)
        self.draw_bevel_rect(surface, panel, raised=False)

        clock_str = self.game_clock_string(game.night_elapsed)
        clock_surf = self.font_large.render(clock_str, True, cfg.WIN95_TEXT)
        surface.blit(clock_surf, (24, panel.top + 18))
        night_surf = self.font_small.render(f"NOITE {game.night_number}", True, cfg.WIN95_TEXT_DIM)
        surface.blit(night_surf, (24, panel.top + 68))

        active_room = game.camera_system.active_camera
        blackout = game.camera_system.is_blackout
        bar_rects = self.stability_bar_rects(len(game.patients), panel.top)
        buttons = self.patient_protocol_rects(len(game.patients), panel.top)
        for i, (patient, rect, button) in enumerate(zip(game.patients, bar_rects, buttons)):
            visible = (patient.room == active_room) and not patient.is_hidden and not blackout
            enabled = visible and patient.can_start_protocol()
            button_text = f"Estabilizar [{i + 1}]"
            if patient.on_protocol_cooldown():
                button_text = f"Recarga: {patient.protocol_cooldown:.0f}s"
            elif not visible:
                button_text = "Localize o paciente"
            elif not enabled:
                button_text = "Protocolo indisponível"
            self.draw_bevel_rect(surface, button, raised=enabled)
            color = (0, 87, 53) if enabled else cfg.WIN95_TEXT_DIM
            label = self.font_medium.render(button_text, True, color)
            surface.blit(label, label.get_rect(center=button.center))
            if not visible:
                self.draw_stability_bar_locked(surface, rect, patient.name, patient)
                continue
            self.draw_stability_bar(surface, rect, patient.name, patient.stability, patient.state)
            if patient.on_protocol_cooldown():
                text = "Aguarde a recarga deste paciente"
                color = cfg.WIN95_TEXT_DIM
            elif patient.can_start_protocol():
                recommended = patient.needs_protocol()
                text = "Protocolo recomendado" if recommended else "Protocolo disponível"
                color = (118, 65, 0) if recommended else (0, 87, 53)
            else:
                text, color = "Protocolo indisponível", cfg.WIN95_TEXT_DIM
            surface.blit(self.font_medium.render(text, True, color), (rect.left, rect.bottom + 6))

        hint = self.font_small.render(
            "Clique nas abas e botões · Atalhos: F1–F5 / 1–2 / R / F / ESC",
            True, cfg.WIN95_TEXT_DIM)
        surface.blit(hint, (cfg.WIDTH - hint.get_width() - 24, panel.top + 18))

        cam_label = self.font_medium.render(game.camera_system.active_camera, True, (0, 87, 53))
        surface.blit(cam_label, (cfg.WIDTH - cam_label.get_width() - 24, panel.top + 42))

        log_y = panel.top + 78
        for text, life in game.event_manager.log_messages[-2:]:
            alpha = min(255, int(life * 90))
            log_surf = self.font_small.render(f"• {text}", True, cfg.COLOR_TEXT_DIM)
            log_surf.set_alpha(alpha)
            surface.blit(log_surf, (cfg.WIDTH - log_surf.get_width() - 24, log_y))
            log_y += 18

    # ------------------------------------------------------------------
    def camera_tab_rects(self, count, top):
        """Geometria das abas de câmera — usada tanto pra desenhar quanto
        pra detectar clique do mouse nelas (game.py)."""
        tab_w = 170
        return [pygame.Rect(12 + i * (tab_w + 8), top, tab_w, 32) for i in range(count)]

    def draw_camera_tabs(self, surface, camera_system, top=12):
        on_cooldown = camera_system.switch_cooldown > 0
        rects = self.camera_tab_rects(len(camera_system.cameras), top)
        for i, (cam, rect) in enumerate(zip(camera_system.cameras, rects)):
            active = i == camera_system.active_index
            # botão "apertado" (afundado) quando é a câmera ativa —
            # mesma linguagem de um toggle button clássico do Windows 95
            self.draw_bevel_rect(surface, rect, raised=not active)
            text_color = cfg.WIN95_TEXT
            offset = (1, 1) if active else (0, 0)
            name = "FARMÁCIA" if cam == cfg.PHARMACY_CAMERA else cam
            label = self.font_medium.render(f"F{i + 1}  {name}", True, text_color)
            surface.blit(label, (rect.left + 10 + offset[0], rect.top + 8 + offset[1]))

            if on_cooldown and not active:
                dim = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                dim.fill((255, 255, 255, 90))
                surface.blit(dim, rect.topleft)

    # ------------------------------------------------------------------
    @staticmethod
    def protocol_window_rect():
        box = pygame.Rect(0, 0, 640, 420)
        box.center = (cfg.WIDTH // 2, cfg.HEIGHT // 2)
        return box

    @classmethod
    def protocol_close_rect(cls):
        box = cls.protocol_window_rect()
        return pygame.Rect(box.right - 25, box.top + 7, 18, 18)

    @classmethod
    def protocol_hold_rect(cls):
        box = cls.protocol_window_rect()
        return pygame.Rect(box.left + 26, box.bottom - 108, 392, 56)

    @classmethod
    def protocol_cancel_rect(cls):
        box = cls.protocol_window_rect()
        return pygame.Rect(box.right - 198, box.bottom - 108, 172, 56)

    def draw_protocol_overlay(self, surface, patient, holding=False):
        overlay = pygame.Surface((cfg.WIDTH, cfg.HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 14, 18, 255))
        surface.blit(overlay, (0, 0))

        box = self.protocol_window_rect()
        title_bar, body, _close = self.draw_window_chrome(
            surface, box, f"Protocolo — {patient.name}", active=True)

        instr = self.font_medium.render("Segure o botão abaixo ou [ESPAÇO]", True, cfg.WIN95_TEXT)
        surface.blit(instr, (body.centerx - instr.get_width() // 2, body.top + 6))

        # barra de PROGRESSO do protocolo — "afundada" (viewport de conteúdo)
        bar_rect = pygame.Rect(body.left + 20, body.top + 64, body.width - 40, 24)
        self.draw_bevel_rect(surface, bar_rect, raised=False, face=cfg.WIN95_FACE_LIGHT)
        progress = min(1.0, patient.protocol_progress / cfg.PROTOCOL_HOLD_SECONDS)
        inner_bar = bar_rect.inflate(-4, -4)
        fill_w = int(inner_bar.width * progress)
        if fill_w > 0:
            pygame.draw.rect(surface, cfg.COLOR_ACCENT, (inner_bar.left, inner_bar.top, fill_w, inner_bar.height))
        prog_label = self.font_small.render(
            f"progresso: {patient.protocol_progress:.1f} / {cfg.PROTOCOL_HOLD_SECONDS:g}s",
            True, cfg.WIN95_TEXT_DIM)
        surface.blit(prog_label, (bar_rect.left, bar_rect.top - 18))

        # barra de ESTABILIDADE, correndo contra o progresso — é a "corrida"
        # que exige precisão: se ela zerar antes do progresso completar, falha.
        stab_rect = pygame.Rect(body.left + 20, body.top + 126, body.width - 40, 24)
        self.draw_bevel_rect(surface, stab_rect, raised=False, face=cfg.WIN95_FACE_LIGHT)
        stab_frac = max(0.0, patient.stability / cfg.STABILITY_MAX)
        danger = stab_frac < 0.18
        stab_color = cfg.COLOR_DANGER if danger else cfg.COLOR_WARNING
        inner_stab = stab_rect.inflate(-4, -4)
        stab_fill_w = int(inner_stab.width * stab_frac)
        if stab_fill_w > 0:
            pygame.draw.rect(surface, stab_color, (inner_stab.left, inner_stab.top, stab_fill_w, inner_stab.height))
        if danger:
            blink = int(self._t * 8) % 2 == 0
            if blink:
                pygame.draw.rect(surface, cfg.COLOR_DANGER, stab_rect, 2)
        stab_label = self.font_small.render("estabilidade restante", True, cfg.WIN95_TEXT_DIM)
        surface.blit(stab_label, (stab_rect.left, stab_rect.top - 18))

        cooldown = self.font_small.render(
            f"Recarga: {cfg.PROTOCOL_COOLDOWN_SECONDS:.0f}s ao concluir / "
            f"{cfg.PROTOCOL_CANCEL_COOLDOWN_SECONDS:.0f}s ao cancelar",
            True, cfg.WIN95_TEXT_DIM)
        surface.blit(cooldown, (body.centerx - cooldown.get_width() // 2, body.top + 174))
        warning = self.font_small.render("A noite continua. Câmeras bloqueadas.", True, cfg.WIN95_TEXT_DIM)
        surface.blit(warning, (body.centerx - warning.get_width() // 2, body.top + 198))

        hold = self.protocol_hold_rect()
        self.draw_bevel_rect(surface, hold, raised=not holding,
                             face=(174, 205, 182) if holding else cfg.WIN95_FACE_LIGHT)
        hold_text = "Estabilizando..." if holding else "Clique e segure para estabilizar"
        label = self.font_medium.render(hold_text, True, (0, 72, 44))
        surface.blit(label, label.get_rect(center=hold.center))
        cancel = self.protocol_cancel_rect()
        self.draw_bevel_rect(surface, cancel)
        label = self.font_medium.render("Cancelar [ESC]", True, cfg.WIN95_TEXT)
        surface.blit(label, label.get_rect(center=cancel.center))
        hint = self.font_small.render("Soltar ou sair do botão interrompe o avanço.", True, cfg.WIN95_TEXT_DIM)
        surface.blit(hint, (body.centerx - hint.get_width() // 2, body.bottom - 26))

    # ------------------------------------------------------------------
    def draw_light_flicker(self, surface):
        overlay = pygame.Surface((cfg.WIDTH, cfg.HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 20))
        surface.blit(overlay, (0, 0))

    # ------------------------------------------------------------------
    def draw_jumpscare(self, surface, progress):
        """Arte raster em tela cheia; escalas preparadas antes da partida."""
        surface.fill((0, 0, 0))
        if self._scare_frames:
            index = min(len(self._scare_frames) - 1, int(max(0, progress) * len(self._scare_frames)))
            frame = self._scare_frames[index]
            frame.set_alpha(int(255 * min(1, max(0, progress) / 0.25)))
            surface.blit(frame, (0, 0))
        else:
            # Falha de arquivo: mantém a transição legível sem reconstruir um rosto geométrico.
            label = self.font_title.render("SINAL PERDIDO", True, (175, 175, 175))
            surface.blit(label, label.get_rect(center=surface.get_rect().center))

    def _prepare_scare_frames(self):
        # Prepara os frames a partir da arte original, com o visual fixo.
        self._scare_frames = []
        width, height = self._jumpscare_sprite.get_size()
        base_scale = max(cfg.WIDTH / width, cfg.HEIGHT / height)
        for zoom in (1.0, 1.025, 1.05, 1.075):
            size = (max(cfg.WIDTH, round(width * base_scale * zoom)),
                    max(cfg.HEIGHT, round(height * base_scale * zoom)))
            scaled = pygame.transform.smoothscale(self._jumpscare_sprite, size)
            crop = pygame.Rect((size[0] - cfg.WIDTH) // 2, (size[1] - cfg.HEIGHT) // 2,
                               cfg.WIDTH, cfg.HEIGHT)
            frame = scaled.subsurface(crop).copy()
            self.pixelation.apply(frame)
            self._scare_frames.append(frame)

    # ------------------------------------------------------------------
    # ---------- "CHROME" ESTILO WINDOWS 95 ----------
    # Tudo que não é o feed de câmera em si (que mantém seu próprio
    # visual "gravado", em camera_system.py) usa esse vocabulário: relevo
    # 3D duplo (claro num canto, escuro no oposto), botões cinza,
    # barra de título azul. Nada de brilho/glow/opacidade suave —
    # a estética é sólida e "quadrada" de propósito.

    def draw_bevel_rect(self, surface, rect, raised=True, face=None):
        """O relevo 3D clássico: borda dupla, clara num canto e escura no
        oposto. raised=True = botão "pra fora" (padrão); raised=False =
        painel "afundado" (viewport de conteúdo, campo de texto etc)."""
        face = face or cfg.WIN95_FACE
        pygame.draw.rect(surface, face, rect)

        hi_outer = cfg.WIN95_HILIGHT if raised else cfg.WIN95_DARK_SHADOW
        sh_outer = cfg.WIN95_DARK_SHADOW if raised else cfg.WIN95_HILIGHT
        hi_inner = cfg.WIN95_FACE_LIGHT if raised else cfg.WIN95_SHADOW
        sh_inner = cfg.WIN95_SHADOW if raised else cfg.WIN95_FACE_LIGHT

        r = rect
        pygame.draw.line(surface, hi_outer, (r.left, r.top), (r.right - 1, r.top))
        pygame.draw.line(surface, hi_outer, (r.left, r.top), (r.left, r.bottom - 1))
        pygame.draw.line(surface, sh_outer, (r.left, r.bottom - 1), (r.right - 1, r.bottom - 1))
        pygame.draw.line(surface, sh_outer, (r.right - 1, r.top), (r.right - 1, r.bottom - 1))

        ri = r.inflate(-2, -2)
        if ri.width > 0 and ri.height > 0:
            pygame.draw.line(surface, hi_inner, (ri.left, ri.top), (ri.right - 1, ri.top))
            pygame.draw.line(surface, hi_inner, (ri.left, ri.top), (ri.left, ri.bottom - 1))
            pygame.draw.line(surface, sh_inner, (ri.left, ri.bottom - 1), (ri.right - 1, ri.bottom - 1))
            pygame.draw.line(surface, sh_inner, (ri.right - 1, ri.top), (ri.right - 1, ri.bottom - 1))

    def _draw_dotted_rect(self, surface, rect, color):
        """Retângulo pontilhado — o indicador clássico de 'foco do
        teclado' num botão selecionado."""
        for x in range(rect.left, rect.right, 4):
            pygame.draw.line(surface, color, (x, rect.top), (min(x + 2, rect.right - 1), rect.top))
            pygame.draw.line(surface, color, (x, rect.bottom - 1), (min(x + 2, rect.right - 1), rect.bottom - 1))
        for y in range(rect.top, rect.bottom, 4):
            pygame.draw.line(surface, color, (rect.left, y), (rect.left, min(y + 2, rect.bottom - 1)))
            pygame.draw.line(surface, color, (rect.right - 1, y), (rect.right - 1, min(y + 2, rect.bottom - 1)))

    def draw_window_chrome(self, surface, rect, title, active=True, closable=True):
        """Moldura de uma 'janela': relevo externo + barra de título azul
        com ícone/título/botão fechar. Retorna (title_bar, body,
        close_btn) pra quem chamou posicionar conteúdo/testar cliques."""
        self.draw_bevel_rect(surface, rect, raised=True)

        title_bar = pygame.Rect(rect.left + 3, rect.top + 3, rect.width - 6, 26)
        title_color = cfg.WIN95_TITLE_ACTIVE if active else cfg.WIN95_SHADOW
        pygame.draw.rect(surface, title_color, title_bar)

        icon_rect = pygame.Rect(title_bar.left + 4, title_bar.top + 5, 16, 16)
        pygame.draw.rect(surface, cfg.WIN95_FACE, icon_rect)
        pygame.draw.rect(surface, cfg.WIN95_DARK_SHADOW, icon_rect, 1)

        title_surf = self.font_medium.render(title, True, cfg.WIN95_TITLE_TEXT)
        surface.blit(title_surf, (icon_rect.right + 6, title_bar.centery - title_surf.get_height() // 2))

        close_btn = pygame.Rect(title_bar.right - 22, title_bar.top + 4, 18, 18)
        if closable:
            self.draw_bevel_rect(surface, close_btn, raised=True)
            x_surf = self.font_small.render("X", True, cfg.WIN95_TEXT)
            surface.blit(x_surf, (close_btn.centerx - x_surf.get_width() // 2,
                                   close_btn.centery - x_surf.get_height() // 2 - 1))

        body = pygame.Rect(rect.left + 6, title_bar.bottom + 4, rect.width - 12,
                            rect.bottom - title_bar.bottom - 10)
        pygame.draw.rect(surface, cfg.WIN95_FACE, body)

        return title_bar, body, close_btn

    @staticmethod
    def fullscreen_button_rect():
        return pygame.Rect(cfg.WIDTH - 296, cfg.HEIGHT - cfg.TASKBAR_HEIGHT + 3,
                           174, cfg.TASKBAR_HEIGHT - 6)

    def draw_taskbar(self, surface):
        """Rodapé sem menu decorativo; relógio e controle de tela cheia."""
        taskbar_h = cfg.TASKBAR_HEIGHT
        taskbar = pygame.Rect(0, cfg.HEIGHT - taskbar_h, cfg.WIDTH, taskbar_h)
        self.draw_bevel_rect(surface, taskbar, raised=True)

        fullscreen_btn = self.fullscreen_button_rect()
        self.draw_bevel_rect(surface, fullscreen_btn)
        text = "Janela [F11]" if self.fullscreen else "Tela cheia [F11]"
        label = self.font_small.render(text, True, cfg.WIN95_TEXT)
        surface.blit(label, label.get_rect(center=fullscreen_btn.center))

        clock_box = pygame.Rect(cfg.WIDTH - 110, taskbar.top + 5, 100, taskbar_h - 10)
        self.draw_bevel_rect(surface, clock_box, raised=False)
        now_txt = datetime.datetime.now().strftime("%H:%M")
        clock_surf = self.font_small.render(now_txt, True, cfg.WIN95_TEXT)
        surface.blit(clock_surf, (clock_box.centerx - clock_surf.get_width() // 2,
                                   clock_box.centery - clock_surf.get_height() // 2))
        return taskbar

    # ------------------------------------------------------------------
    @staticmethod
    def menu_window_rect():
        rect = pygame.Rect(0, 0, 620, 520)
        rect.center = (cfg.WIDTH // 2, (cfg.HEIGHT - cfg.TASKBAR_HEIGHT) // 2)
        return rect

    @classmethod
    def menu_close_rect(cls):
        rect = cls.menu_window_rect()
        return pygame.Rect(rect.right - 25, rect.top + 7, 18, 18)

    def menu_option_rects(self, count):
        """Geometria dos botões do menu — usada tanto por draw_menu quanto
        pelo hit-test de clique do mouse em game.py, pra nunca ficarem
        dessincronizadas. Depende só da quantidade de opções."""
        win = self.menu_window_rect()
        body_top = win.top + 3 + 26 + 4       # mesma conta de draw_window_chrome
        body_bottom = win.bottom - 6
        body_left = win.left + 6
        body_right = win.right - 6
        sep_y = body_top + 116

        btn_w, btn_h, gap = 320, 46, 14
        total_h = count * btn_h + (count - 1) * gap
        avail_top = sep_y + 24
        avail_bottom = body_bottom - 20
        start_y = avail_top + max(0, (avail_bottom - avail_top - total_h) // 2)

        rects = []
        for i in range(count):
            r = pygame.Rect(0, 0, btn_w, btn_h)
            r.center = ((body_left + body_right) // 2, start_y + i * (btn_h + gap) + btn_h // 2)
            rects.append(r)
        return rects

    # ------------------------------------------------------------------
    def draw_menu(self, surface, selected_option=0, options=None):
        surface.fill(cfg.WIN95_DESKTOP_TEAL)
        self.draw_taskbar(surface)

        win = self.menu_window_rect()
        _title_bar, body, _close_btn = self.draw_window_chrome(surface, win, "Turno Noturno — Configuração")

        big = self.font_title.render("TURNO NOTURNO", True, cfg.WIN95_TEXT)
        surface.blit(big, (body.centerx - big.get_width() // 2, body.top + 18))
        sub = self.font_medium.render("Centro de Observação Clínica", True, cfg.WIN95_TEXT_DIM)
        surface.blit(sub, (body.centerx - sub.get_width() // 2, body.top + 76))

        sep_y = body.top + 116
        pygame.draw.line(surface, cfg.WIN95_SHADOW, (body.left + 16, sep_y), (body.right - 16, sep_y))
        pygame.draw.line(surface, cfg.WIN95_HILIGHT, (body.left + 16, sep_y + 1), (body.right - 16, sep_y + 1))

        # options vem de game.py como lista de (action, label); aceitamos
        # também uma lista simples de strings pra manter compatibilidade.
        options = options or [("continue", "Iniciar turno"), ("quit", "Sair")]
        labels = [o[1] if isinstance(o, tuple) else o for o in options]
        option_rects = self.menu_option_rects(len(labels))

        for i, (opt, r) in enumerate(zip(labels, option_rects)):
            pressed = (i == selected_option)
            self.draw_bevel_rect(surface, r, raised=not pressed)
            offset = (1, 1) if pressed else (0, 0)
            txt = self.font_medium.render(opt, True, cfg.WIN95_TEXT)
            surface.blit(txt, (r.centerx - txt.get_width() // 2 + offset[0],
                                r.centery - txt.get_height() // 2 + offset[1]))
            if pressed:
                self._draw_dotted_rect(surface, r.inflate(-8, -8), cfg.WIN95_TEXT)

        hint = self.font_small.render("Jogue só com o mouse ou só com o teclado", True, cfg.WIN95_TEXT_DIM)
        surface.blit(hint, (body.centerx - hint.get_width() // 2, body.bottom - 22))

    # ------------------------------------------------------------------
    def draw_night_intro(self, surface, night_number):
        surface.fill(cfg.WIN95_DESKTOP_TEAL)
        self.draw_taskbar(surface)

        win = pygame.Rect(0, 0, 700, 420)
        win.center = (cfg.WIDTH // 2, (cfg.HEIGHT - 34) // 2)
        _title_bar, body, _close_btn = self.draw_window_chrome(surface, win, "Aviso do sistema")

        msg = self.font_large.render(f"NOITE {night_number}", True, cfg.WIN95_TEXT)
        surface.blit(msg, (body.centerx - msg.get_width() // 2, body.top + 14))

        # caixa de texto "afundada" com a lore sendo digitada aos poucos —
        # mesmo visual de um campo de notas do sistema.
        box = pygame.Rect(body.left + 20, body.top + 70, body.width - 40, body.height - 150)
        self.draw_bevel_rect(surface, box, raised=False, face=cfg.WIN95_FACE_LIGHT)
        inner = box.inflate(-16, -16)

        revealed_n = max(0, int(self._lore_reveal_chars))
        revealed = self._lore_text[:revealed_n]
        lines = self._wrap_text(revealed, self.font_small, inner.width)
        y = inner.top
        for line in lines:
            line_surf = self.font_small.render(line, True, cfg.WIN95_TEXT)
            surface.blit(line_surf, (inner.left, y))
            y += 20

        if not self._lore_full:
            blink = int(self._t * 6) % 2 == 0
            if blink:
                last_w = self.font_small.size(lines[-1])[0] if lines else 0
                cursor = self.font_small.render("▌", True, cfg.WIN95_TEXT)
                surface.blit(cursor, (inner.left + last_w + 2, y - 20))

        if night_number > 1:
            flavor = self.font_small.render(
                "Os pacientes estão mais instáveis esta noite. Fique atento.",
                True, cfg.WIN95_TEXT_DIM)
            surface.blit(flavor, (body.centerx - flavor.get_width() // 2, box.bottom + 8))

        ok_btn = pygame.Rect(0, 0, 130, 36)
        ok_btn.center = (body.centerx, body.bottom - 30)
        self.draw_bevel_rect(surface, ok_btn, raised=True)
        ok_txt = self.font_medium.render("OK", True, cfg.WIN95_TEXT)
        surface.blit(ok_txt, (ok_btn.centerx - ok_txt.get_width() // 2, ok_btn.centery - ok_txt.get_height() // 2))
        self._draw_dotted_rect(surface, ok_btn.inflate(-8, -8), cfg.WIN95_TEXT)

        if self._lore_full:
            hint_text = "Pressione ENTER para começar"
        else:
            hint_text = "ENTER para revelar tudo de uma vez"
        hint = self.font_small.render(hint_text, True, cfg.WIN95_TEXT_DIM)
        surface.blit(hint, (body.centerx - hint.get_width() // 2, ok_btn.top - 22))

    @staticmethod
    def _wrap_text(text, font, max_width):
        """Quebra de linha simples respeitando quebras já existentes
        (\\n) e o limite de largura em pixels."""
        lines = []
        for paragraph in text.split("\n"):
            words = paragraph.split(" ")
            current = ""
            for word in words:
                trial = f"{current} {word}".strip()
                if font.size(trial)[0] <= max_width or not current:
                    current = trial
                else:
                    lines.append(current)
                    current = word
            lines.append(current)
        return lines or [""]

    # ------------------------------------------------------------------
    @staticmethod
    def end_window_rect(won=False, has_report=False):
        win = pygame.Rect(0, 0, 960, 780 if not won and has_report else 320)
        win.center = (cfg.WIDTH // 2, (cfg.HEIGHT - cfg.TASKBAR_HEIGHT) // 2)
        return win

    @classmethod
    def end_return_rect(cls, won=False, has_report=False):
        win = cls.end_window_rect(won, has_report)
        button = pygame.Rect(0, 0, 260, 44)
        button.center = (win.centerx, win.bottom - 46)
        return button

    @classmethod
    def end_close_rect(cls, won=False, has_report=False):
        win = cls.end_window_rect(won, has_report)
        return pygame.Rect(win.right - 25, win.top + 7, 18, 18)

    def draw_end_screen(self, surface, won, night_number, final_night, report=None, delivered=0):
        surface.fill(cfg.WIN95_DESKTOP_TEAL)
        self.draw_taskbar(surface)

        win = self.end_window_rect(won, bool(report))
        title = "Turno concluído" if won else "Turno interrompido"
        _title_bar, body, _close_btn = self.draw_window_chrome(surface, win, title, active=won)

        if won:
            msg = "TURNO CONCLUÍDO"
            sub = f"Ambos os pacientes chegaram ao amanhecer. Entregas concluídas: {delivered}."
        else:
            msg = "TURNO INTERROMPIDO"
            sub = "A estabilidade de um paciente chegou a zero."

        msg_surf = self.font_large.render(msg, True, cfg.WIN95_TEXT)
        surface.blit(msg_surf, (body.centerx - msg_surf.get_width() // 2, body.top + 24))
        sub_surf = self.font_small.render(sub, True, cfg.WIN95_TEXT_DIM)
        surface.blit(sub_surf, (body.centerx - sub_surf.get_width() // 2, body.top + 74))

        if not won and report:
            report_box = pygame.Rect(body.left + 28, body.top + 112, body.width - 56, body.height - 225)
            self.draw_bevel_rect(surface, report_box, raised=False, face=cfg.WIN95_FACE_LIGHT)
            x, y = report_box.left + 18, report_box.top + 14
            lines = [f"Interrupção às {self.game_clock_string(report['seconds'])}"]
            lines.extend(report["causes"])
            lines.extend(report["details"])
            lines.append("Últimos acontecimentos relevantes:")
            lines.extend(f"{self.game_clock_string(e['seconds'])} — {e['text']}" for e in report["events"])
            lines.append(f"Entregas: {report['delivered']}   |   Pedidos expirados: {report['expired']}")
            self._care_text(surface, "\n".join(lines),
                            pygame.Rect(x, y, report_box.width - 36, report_box.height - 28), line_height=27)

        ok_btn = self.end_return_rect(won, bool(report))
        self.draw_bevel_rect(surface, ok_btn, raised=True)
        ok_txt = self.font_medium.render("Voltar ao menu", True, cfg.WIN95_TEXT)
        surface.blit(ok_txt, (ok_btn.centerx - ok_txt.get_width() // 2, ok_btn.centery - ok_txt.get_height() // 2))
        self._draw_dotted_rect(surface, ok_btn.inflate(-8, -8), cfg.WIN95_TEXT)

        if won and night_number < final_night:
            hint = "ENTER ou clique para continuar"
        else:
            hint = "ENTER ou clique para voltar ao menu"
        hint_surf = self.font_small.render(hint, True, cfg.WIN95_TEXT_DIM)
        surface.blit(hint_surf, (body.centerx - hint_surf.get_width() // 2, ok_btn.top - 22))
