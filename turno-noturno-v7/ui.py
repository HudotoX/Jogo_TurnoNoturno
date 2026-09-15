"""
ui.py
Todo o desenho de interface que não é o feed de câmera em si:
HUD (relógio, estabilidade, prompts), telas de menu, intro de noite,
tela de game over e tela de vitória.

Suporte a assets reais: se existir uma fonte em
  assets/fonts/main.ttf
ela é usada em todo o jogo no lugar da fonte padrão do sistema. Se
existir uma imagem em
  assets/backgrounds/menu.png
ela é usada como fundo do menu/telas de transição no lugar da textura
gerada por código. Em ambos os casos, não é preciso mudar nada aqui —
só colocar o arquivo com esse nome na pasta.
"""

import math
import os
import random
import pygame
import settings as cfg

FONTS_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")
BACKGROUNDS_DIR = os.path.join(os.path.dirname(__file__), "assets", "backgrounds")
SPRITES_DIR = os.path.join(os.path.dirname(__file__), "assets", "sprites")
CUSTOM_FONT_PATH = os.path.join(FONTS_DIR, "main.ttf")
MENU_BG_PATH = os.path.join(BACKGROUNDS_DIR, "menu.png")
JUMPSCARE_SPRITE_PATH = os.path.join(SPRITES_DIR, "jumpscare.png")


def load_font(size, bold=False):
    """Carrega a fonte customizada se existir; senão cai na fonte do sistema."""
    if os.path.isfile(CUSTOM_FONT_PATH):
        try:
            return pygame.font.Font(CUSTOM_FONT_PATH, size)
        except pygame.error:
            pass
    return pygame.font.SysFont(cfg.FONT_NAME, size, bold=bold)


class UI:
    def __init__(self):
        self.font_small = load_font(16)
        self.font_medium = load_font(22, bold=True)
        self.font_large = load_font(40, bold=True)
        self.font_title = load_font(58, bold=True)
        self._t = 0.0
        self._static_dots = [
            (random.randint(0, cfg.WIDTH), random.randint(0, cfg.HEIGHT), random.random())
            for _ in range(70)
        ]
        self._menu_bg = None
        if os.path.isfile(MENU_BG_PATH):
            try:
                self._menu_bg = pygame.image.load(MENU_BG_PATH).convert()
            except pygame.error:
                self._menu_bg = None

        self._jumpscare_sprite = None
        if os.path.isfile(JUMPSCARE_SPRITE_PATH):
            try:
                self._jumpscare_sprite = pygame.image.load(JUMPSCARE_SPRITE_PATH).convert_alpha()
            except pygame.error:
                self._jumpscare_sprite = None

        # pré-computados uma única vez (mais barato que refazer todo frame):
        # vinheta radial das telas de menu/intro/fim, e uma grade fina de
        # scanlines por cima de tudo, pra reforçar o clima "monitor de
        # vigilância" também fora do feed de câmera.
        self._menu_vignette = self._build_vignette()
        self._menu_scanlines = self._build_static_scanlines()

    def tick(self, dt):
        self._t += dt

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
        shadow = pygame.Rect(rect.left, rect.top + 2, rect.width, rect.height)
        pygame.draw.rect(surface, (0, 0, 0), shadow, border_radius=5)
        pygame.draw.rect(surface, cfg.COLOR_PANEL_LIGHT, rect, border_radius=5)

        fill_w = max(0, int(rect.width * (value / cfg.STABILITY_MAX)))
        color = cfg.STATE_COLORS.get(state, cfg.COLOR_ACCENT)
        if fill_w > 0:
            fill_rect = pygame.Rect(rect.left, rect.top, fill_w, rect.height)
            pygame.draw.rect(surface, color, fill_rect, border_radius=5)
            # brilho superior sutil
            sheen = pygame.Surface((fill_w, max(1, rect.height // 3)), pygame.SRCALPHA)
            sheen.fill((255, 255, 255, 40))
            surface.blit(sheen, (rect.left, rect.top))

        if state in ("ANORMAL", "PERIGO"):
            pulse = 0.5 + 0.5 * math.sin(self._t * 6.0)
            glow_alpha = int(60 + 90 * pulse)
            glow = pygame.Surface((rect.width + 12, rect.height + 12), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*color, glow_alpha), glow.get_rect(), border_radius=8)
            surface.blit(glow, (rect.left - 6, rect.top - 6), special_flags=pygame.BLEND_RGBA_ADD)

        pygame.draw.rect(surface, cfg.COLOR_CAM_BORDER, rect, 2, border_radius=5)

        label_surf = self.font_small.render(f"{label}", True, cfg.COLOR_TEXT)
        state_surf = self.font_small.render(state, True, color)
        surface.blit(label_surf, (rect.left, rect.top - 20))
        surface.blit(state_surf, (rect.right - state_surf.get_width(), rect.top - 20))

    # ------------------------------------------------------------------
    def draw_stability_bar_locked(self, surface, rect, label, patient):
        """Versão 'sem sinal' da barra — desenhada quando o paciente NÃO
        está na câmera ativa no momento. Mostra só um snapshot congelado
        (última leitura real, de quando a câmera esteve nele por último),
        hachurado e dessaturado, pra deixar claro que não é o valor atual.
        É o que dá peso a trocar de câmera: sem olhar, você só sabe como
        ele estava, não como está agora."""
        shadow = pygame.Rect(rect.left, rect.top + 2, rect.width, rect.height)
        pygame.draw.rect(surface, (0, 0, 0), shadow, border_radius=5)
        pygame.draw.rect(surface, cfg.COLOR_PANEL_LIGHT, rect, border_radius=5)

        frac = max(0.0, patient.last_known_stability / cfg.STABILITY_MAX)
        fill_w = max(0, int(rect.width * frac))
        if fill_w > 0:
            stale = pygame.Surface((fill_w, rect.height), pygame.SRCALPHA)
            stale.fill((*cfg.COLOR_TEXT_DIM, 100))
            surface.blit(stale, (rect.left, rect.top))

        # hachura diagonal simples = "sinal não confiável agora"
        hatch = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        step = 11
        for x in range(-rect.height, rect.width, step):
            pygame.draw.line(hatch, (0, 0, 0, 65), (x, rect.height), (x + rect.height, 0), 2)
        surface.blit(hatch, rect.topleft)

        pygame.draw.rect(surface, cfg.COLOR_CAM_BORDER, rect, 2, border_radius=5)

        cam_index = cfg.CAMERAS.index(patient.room) + 1 if patient.room in cfg.CAMERAS else None
        cam_tag = f"CAM {cam_index:02d}" if cam_index else "?"
        label_surf = self.font_small.render(f"{label}", True, cfg.COLOR_TEXT_DIM)
        loc_surf = self.font_small.render(f"sem sinal — {cam_tag}", True, cfg.COLOR_TEXT_DIM)
        surface.blit(label_surf, (rect.left, rect.top - 20))
        surface.blit(loc_surf, (rect.right - loc_surf.get_width(), rect.top - 20))

        concerning = (patient.last_known_state in (cfg.STATE_ANORMAL, cfg.STATE_PERIGO)
                      or patient.last_known_stability <= cfg.PROTOCOL_TRIGGER_THRESHOLD)
        if concerning:
            pulse = 0.5 + 0.5 * math.sin(self._t * 6.0)
            warn = self.font_small.render(
                "última leitura preocupante — verifique essa câmera", True, cfg.COLOR_WARNING)
            warn.set_alpha(int(130 + 100 * pulse))
            surface.blit(warn, (rect.left, rect.bottom + 6))
        else:
            ago_text = f"última leitura há {patient.seconds_since_seen:.0f}s"
            ago_surf = self.font_small.render(ago_text, True, cfg.COLOR_TEXT_DIM)
            surface.blit(ago_surf, (rect.left, rect.bottom + 6))

    # ------------------------------------------------------------------
    def draw_hud(self, surface, game):
        panel = pygame.Rect(0, cfg.HEIGHT - 130, cfg.WIDTH, 130)
        self.draw_vertical_gradient(surface, panel, (16, 18, 24), (10, 11, 15))
        pygame.draw.line(surface, cfg.COLOR_CAM_BORDER, (0, panel.top), (cfg.WIDTH, panel.top), 2)
        glow_line = pygame.Surface((cfg.WIDTH, 2), pygame.SRCALPHA)
        glow_line.fill((*cfg.CRT_GLOW_COLOR, 60))
        surface.blit(glow_line, (0, panel.top - 2))

        clock_str = self.game_clock_string(game.night_elapsed)
        clock_surf = self.font_large.render(clock_str, True, cfg.COLOR_TEXT)
        surface.blit(clock_surf, (24, panel.top + 18))
        night_surf = self.font_small.render(f"NOITE {game.night_number}", True, cfg.COLOR_TEXT_DIM)
        surface.blit(night_surf, (24, panel.top + 68))

        bar_w = 250
        x0 = 210
        active_room = game.camera_system.active_camera
        blackout = game.camera_system.is_blackout
        for i, patient in enumerate(game.patients):
            rect = pygame.Rect(x0 + i * (bar_w + 40), panel.top + 32, bar_w, 20)
            visible = (patient.room == active_room) and not patient.is_hidden and not blackout
            if not visible:
                self.draw_stability_bar_locked(surface, rect, patient.name, patient)
                continue
            self.draw_stability_bar(surface, rect, patient.name, patient.stability, patient.state)
            if patient.needs_protocol():
                blink = int(self._t * 3) % 2 == 0
                if blink:
                    warn = self.font_small.render(
                        f"Pressione [{i + 1}] para iniciar protocolo", True, cfg.COLOR_WARNING)
                    surface.blit(warn, (rect.left, rect.bottom + 6))
            elif patient.on_protocol_cooldown():
                cd = self.font_small.render(
                    f"Protocolo em recarga ({patient.protocol_cooldown:.0f}s)", True, cfg.COLOR_TEXT_DIM)
                surface.blit(cd, (rect.left, rect.bottom + 6))

        hint = self.font_small.render(
            "Setas/A-D: câmera   1/2: protocolo   R: responder chamado   ESC: pausar   "
            "(estabilidade só é confiável na câmera do paciente)",
            True, cfg.COLOR_TEXT_DIM)
        surface.blit(hint, (cfg.WIDTH - hint.get_width() - 24, panel.top + 18))

        cam_label = self.font_medium.render(game.camera_system.active_camera, True, cfg.COLOR_ACCENT)
        surface.blit(cam_label, (cfg.WIDTH - cam_label.get_width() - 24, panel.top + 42))

        log_y = panel.top + 78
        for text, life in game.event_manager.log_messages[-2:]:
            alpha = min(255, int(life * 90))
            log_surf = self.font_small.render(f"• {text}", True, cfg.COLOR_TEXT_DIM)
            log_surf.set_alpha(alpha)
            surface.blit(log_surf, (cfg.WIDTH - log_surf.get_width() - 24, log_y))
            log_y += 18

    # ------------------------------------------------------------------
    def draw_call_banner(self, surface, game):
        """Banner bem visível no topo (independe da câmera ativa) para
        qualquer paciente chamando — é o gancho que obriga o jogador a
        decidir e agir, em vez de só observar passivamente."""
        calling = [p for p in game.patients if p.is_calling]
        if not calling:
            return

        y = 56
        for patient in calling:
            frac = patient.call_time_left()
            pulse = 0.5 + 0.5 * math.sin(self._t * 8.0)
            bar_w = 420
            box = pygame.Rect(cfg.WIDTH // 2 - bar_w // 2, y, bar_w, 34)

            bg = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
            bg.fill((60, 10, 10, 210))
            surface.blit(bg, box.topleft)

            glow = pygame.Surface((box.width + 10, box.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*cfg.COLOR_DANGER, int(70 + 90 * pulse)), glow.get_rect(), border_radius=8)
            surface.blit(glow, (box.left - 5, box.top - 5), special_flags=pygame.BLEND_RGBA_ADD)

            pygame.draw.rect(surface, cfg.COLOR_DANGER, box, 2, border_radius=6)

            fill_w = max(0, int((box.width - 4) * frac))
            fill = pygame.Rect(box.left + 2, box.bottom - 6, fill_w, 4)
            pygame.draw.rect(surface, cfg.COLOR_DANGER, fill)

            text = (f"CHAMADO — {patient.name} em {cfg.ROOM_LABELS.get(patient.room, patient.room)} "
                    f"— vá até lá e aperte [R]")
            text_surf = self.font_small.render(text, True, (255, 235, 235))
            surface.blit(text_surf, (box.centerx - text_surf.get_width() // 2, box.top + 9))

            y += box.height + 8

    # ------------------------------------------------------------------
    def draw_camera_tabs(self, surface, camera_system):
        tab_w = 132
        on_cooldown = camera_system.switch_cooldown > 0
        for i, cam in enumerate(camera_system.cameras):
            rect = pygame.Rect(12 + i * (tab_w + 8), 12, tab_w, 32)
            active = i == camera_system.active_index
            if active:
                pygame.draw.rect(surface, cfg.COLOR_ACCENT, rect, border_radius=5)
                glow = pygame.Surface((rect.width + 8, rect.height + 8), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*cfg.COLOR_ACCENT, 70), glow.get_rect(), border_radius=8)
                surface.blit(glow, (rect.left - 4, rect.top - 4), special_flags=pygame.BLEND_RGBA_ADD)
                text_color = (8, 9, 11)
            else:
                pygame.draw.rect(surface, cfg.COLOR_PANEL_LIGHT, rect, border_radius=5)
                pygame.draw.rect(surface, cfg.COLOR_CAM_BORDER, rect, 1, border_radius=5)
                text_color = cfg.COLOR_TEXT_DIM
            label = self.font_small.render(f"{i + 1}  {cam}", True, text_color)
            surface.blit(label, (rect.left + 10, rect.top + 8))

            if on_cooldown and not active:
                dim = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                dim.fill((0, 0, 0, 90))
                surface.blit(dim, rect.topleft)

    # ------------------------------------------------------------------
    def draw_protocol_overlay(self, surface, patient):
        overlay = pygame.Surface((cfg.WIDTH, cfg.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        box = pygame.Rect(cfg.WIDTH // 2 - 230, cfg.HEIGHT // 2 - 120, 460, 240)
        shadow = box.copy()
        shadow.top += 6
        shadow_surf = pygame.Surface((shadow.width, shadow.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 120), shadow_surf.get_rect(), border_radius=10)
        surface.blit(shadow_surf, shadow.topleft)

        self.draw_vertical_gradient(surface, box, (26, 29, 36), (16, 18, 23))
        pygame.draw.rect(surface, cfg.COLOR_ACCENT, box, 2, border_radius=10)

        title = self.font_medium.render(f"Protocolo de estabilização — {patient.name}", True, cfg.COLOR_TEXT)
        surface.blit(title, (box.centerx - title.get_width() // 2, box.top + 16))

        instr = self.font_small.render("Segure [ESPAÇO] até completar — não solte!", True, cfg.COLOR_TEXT_DIM)
        surface.blit(instr, (box.centerx - instr.get_width() // 2, box.top + 50))

        # barra de PROGRESSO do protocolo
        bar_rect = pygame.Rect(box.left + 30, box.top + 82, box.width - 60, 24)
        pygame.draw.rect(surface, cfg.COLOR_PANEL_LIGHT, bar_rect, border_radius=6)
        progress = min(1.0, patient.protocol_progress / cfg.PROTOCOL_HOLD_SECONDS)
        fill = pygame.Rect(bar_rect.left, bar_rect.top, int(bar_rect.width * progress), bar_rect.height)
        if fill.width > 0:
            pygame.draw.rect(surface, cfg.COLOR_ACCENT, fill, border_radius=6)
            sheen = pygame.Surface((fill.width, fill.height // 2), pygame.SRCALPHA)
            sheen.fill((255, 255, 255, 45))
            surface.blit(sheen, fill.topleft)
        pygame.draw.rect(surface, cfg.COLOR_CAM_BORDER, bar_rect, 2, border_radius=6)
        prog_label = self.font_small.render("progresso", True, cfg.COLOR_TEXT_DIM)
        surface.blit(prog_label, (bar_rect.left, bar_rect.top - 18))

        # barra de ESTABILIDADE, correndo contra o progresso — é a "corrida"
        # que exige precisão: se ela zerar antes do progresso completar, falha.
        stab_rect = pygame.Rect(box.left + 30, box.top + 138, box.width - 60, 24)
        pygame.draw.rect(surface, cfg.COLOR_PANEL_LIGHT, stab_rect, border_radius=6)
        stab_frac = max(0.0, patient.stability / cfg.STABILITY_MAX)
        danger = stab_frac < 0.18
        stab_color = cfg.COLOR_DANGER if danger else cfg.COLOR_WARNING
        stab_fill = pygame.Rect(stab_rect.left, stab_rect.top, int(stab_rect.width * stab_frac), stab_rect.height)
        if stab_fill.width > 0:
            pygame.draw.rect(surface, stab_color, stab_fill, border_radius=6)
        if danger:
            pulse = 0.5 + 0.5 * math.sin(self._t * 10.0)
            glow = pygame.Surface((stab_rect.width + 10, stab_rect.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*cfg.COLOR_DANGER, int(80 + 100 * pulse)), glow.get_rect(), border_radius=8)
            surface.blit(glow, (stab_rect.left - 5, stab_rect.top - 5), special_flags=pygame.BLEND_RGBA_ADD)
        pygame.draw.rect(surface, cfg.COLOR_CAM_BORDER, stab_rect, 2, border_radius=6)
        stab_label = self.font_small.render("estabilidade restante", True, cfg.COLOR_TEXT_DIM)
        surface.blit(stab_label, (stab_rect.left, stab_rect.top - 18))

        cancel = self.font_small.render("[ESC] cancelar", True, cfg.COLOR_TEXT_DIM)
        surface.blit(cancel, (box.centerx - cancel.get_width() // 2, box.bottom - 26))

    # ------------------------------------------------------------------
    def draw_light_flicker(self, surface):
        overlay = pygame.Surface((cfg.WIDTH, cfg.HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 20))
        surface.blit(overlay, (0, 0))

    # ------------------------------------------------------------------
    def draw_jumpscare(self, surface, progress):
        """progress vai de 1.0 (início do susto) a 0.0 (fim). O pico visual
        acontece logo no início e depois esvanece rápido."""
        intensity = min(1.0, progress / 0.35) if progress > 0.65 else progress / 0.65

        flash = pygame.Surface((cfg.WIDTH, cfg.HEIGHT), pygame.SRCALPHA)
        flash.fill((255, 30, 30, int(120 * intensity)))
        surface.blit(flash, (0, 0))

        if self._jumpscare_sprite is not None:
            scale = 1.0 + 0.15 * intensity
            w = int(self._jumpscare_sprite.get_width() * scale)
            h = int(self._jumpscare_sprite.get_height() * scale)
            scaled = pygame.transform.smoothscale(self._jumpscare_sprite, (max(1, w), max(1, h)))
            rect = scaled.get_rect(center=(cfg.WIDTH // 2, cfg.HEIGHT // 2))
            surface.blit(scaled, rect.topleft)
        else:
            self._draw_placeholder_scare_face(surface, intensity)

    def _draw_placeholder_scare_face(self, surface, intensity):
        """Rosto simples desenhado só com formas — troque por
        assets/sprites/jumpscare.png quando tiverem a arte pronta."""
        cx, cy = cfg.WIDTH // 2, cfg.HEIGHT // 2
        size = int(220 + 40 * intensity)
        face = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(face, (235, 230, 225, 235), (size * 0.3, size * 0.15, size * 1.4, size * 1.7))

        eye_w, eye_h = size * 0.22, size * 0.34
        left_eye = pygame.Rect(0, 0, eye_w, eye_h)
        left_eye.center = (size * 0.62, size * 0.68)
        right_eye = left_eye.copy()
        right_eye.center = (size * 1.38, size * 0.68)
        pygame.draw.ellipse(face, (10, 10, 10, 255), left_eye)
        pygame.draw.ellipse(face, (10, 10, 10, 255), right_eye)
        pygame.draw.ellipse(face, (170, 20, 20, 220), left_eye.inflate(-eye_w * 0.55, -eye_h * 0.4))
        pygame.draw.ellipse(face, (170, 20, 20, 220), right_eye.inflate(-eye_w * 0.55, -eye_h * 0.4))

        mouth = pygame.Rect(0, 0, size * 0.5, size * 0.65)
        mouth.center = (size, size * 1.35)
        pygame.draw.ellipse(face, (15, 4, 4, 255), mouth)
        for i in range(6):
            tx = mouth.left + (i + 0.5) * mouth.width / 6
            pygame.draw.polygon(face, (240, 240, 235, 255),
                                 [(tx - 6, mouth.top), (tx + 6, mouth.top), (tx, mouth.top + 22)])

        surface.blit(face, (cx - size, cy - size))

    # ------------------------------------------------------------------
    def _build_vignette(self):
        """Vinheta radial pré-renderizada uma única vez: escurece os
        cantos, mantém o centro limpo. Construída com elipses concêntricas
        (de fora pra dentro, alpha decrescente) — cada uma sobrescreve a
        anterior na área que cobre, então o resultado final é um degradê
        suave sem precisar mexer em array de pixels."""
        w, h = cfg.WIDTH, cfg.HEIGHT
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        steps = 34
        max_alpha = 150
        for i in range(steps + 1):
            t = i / steps
            alpha = int(max_alpha * (1 - t))
            shrink = t * 0.92
            rw = max(1, int(cx * (1 - shrink)))
            rh = max(1, int(cy * (1 - shrink)))
            rect = pygame.Rect(0, 0, rw * 2, rh * 2)
            rect.center = (cx, cy)
            pygame.draw.ellipse(surf, (0, 0, 0, alpha), rect)
        return surf

    def _build_static_scanlines(self):
        """Grade de scanlines fixa e bem sutil, cobrindo a tela toda —
        mesma linguagem visual do feed de câmera (camera_system.py), só
        que mais fraca, pra não brigar com o texto do menu."""
        surf = pygame.Surface((cfg.WIDTH, cfg.HEIGHT), pygame.SRCALPHA)
        alpha = max(6, cfg.SCANLINE_ALPHA // 2)
        y = 0
        while y < cfg.HEIGHT:
            pygame.draw.line(surf, (0, 0, 0, alpha), (0, y), (cfg.WIDTH, y))
            y += cfg.SCANLINE_SPACING
        return surf

    def _draw_scan_sweep(self, surface):
        """Uma faixa translúcida bem fraca varrendo a tela de cima a baixo
        em loop lento — o toque de 'monitor ligado' nas telas paradas
        (menu, intro, fim de noite)."""
        band_h = 160
        period = 7.0
        loop_y = (self._t % period) / period * (cfg.HEIGHT + band_h * 2) - band_h
        band = pygame.Surface((cfg.WIDTH, band_h), pygame.SRCALPHA)
        for i in range(band_h):
            a = int(12 * math.sin(math.pi * i / band_h))
            if a <= 0:
                continue
            pygame.draw.line(band, (*cfg.COLOR_ACCENT, a), (0, i), (cfg.WIDTH, i))
        surface.blit(band, (0, int(loop_y)), special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_viewfinder_panel(self, surface, rect, alpha=95):
        """Painel translúcido com cantos em 'mira de câmera' — o mesmo
        vocabulário visual usado nas bordas do feed ao vivo
        (camera_system.py:_draw_border), aplicado aqui pra enquadrar o
        conteúdo das telas de menu/intro/fim como se ainda estivéssemos
        olhando por uma câmera."""
        panel_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        panel_surf.fill((*cfg.COLOR_PANEL, alpha))
        surface.blit(panel_surf, rect.topleft)
        pygame.draw.rect(surface, cfg.COLOR_CAM_BORDER, rect, 1, border_radius=6)

        c = 28
        color = cfg.COLOR_ACCENT
        for x, y, dx, dy in ((rect.left, rect.top, 1, 1), (rect.right, rect.top, -1, 1),
                              (rect.left, rect.bottom, 1, -1), (rect.right, rect.bottom, -1, -1)):
            pygame.draw.line(surface, color, (x, y), (x + c * dx, y), 2)
            pygame.draw.line(surface, color, (x, y), (x, y + c * dy), 2)

    def _draw_lens_icon(self, surface, center, radius=24):
        """Ícone de lente desenhado só com formas (sem asset) — o pulso no
        meio simula uma câmera 'viva', ligada, olhando de volta."""
        pygame.draw.circle(surface, cfg.COLOR_CAM_BORDER, center, radius, 2)
        pygame.draw.circle(surface, cfg.COLOR_ACCENT, center, int(radius * 0.6), 1)
        pulse = 0.5 + 0.5 * math.sin(self._t * 2.0)
        inner_r = max(2, int(radius * 0.2 + radius * 0.08 * pulse))
        pygame.draw.circle(surface, cfg.COLOR_ACCENT, center, inner_r)

    def _draw_rec_tag(self, surface, pos, label="SISTEMA ONLINE"):
        blink = int(self._t * 2) % 2 == 0
        if blink:
            pygame.draw.circle(surface, cfg.COLOR_DANGER, (pos[0], pos[1] + 6), 4)
        tag = self.font_small.render(label, True, cfg.COLOR_TEXT_DIM)
        surface.blit(tag, (pos[0] + 14, pos[1] - 2))

    # ------------------------------------------------------------------
    def _draw_background_texture(self, surface):
        if self._menu_bg is not None:
            scaled = pygame.transform.smoothscale(self._menu_bg, (cfg.WIDTH, cfg.HEIGHT))
            surface.blit(scaled, (0, 0))
            # ainda escurece um pouco embaixo pra garantir contraste do texto
            shade = pygame.Surface((cfg.WIDTH, cfg.HEIGHT), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 90))
            surface.blit(shade, (0, 0))
            return
        self.draw_vertical_gradient(surface, pygame.Rect(0, 0, cfg.WIDTH, cfg.HEIGHT),
                                     cfg.COLOR_BG_TOP, cfg.COLOR_BG_BOTTOM)
        # grade fina de fundo, tipo blueprint, quase invisível
        for x in range(0, cfg.WIDTH, 40):
            pygame.draw.line(surface, cfg.MENU_GRID_COLOR, (x, 0), (x, cfg.HEIGHT), 1)
        for y in range(0, cfg.HEIGHT, 40):
            pygame.draw.line(surface, cfg.MENU_GRID_COLOR, (0, y), (cfg.WIDTH, y), 1)
        # poeira/estática lenta flutuando
        for (x, y, phase) in self._static_dots:
            yy = (y + self._t * 12) % cfg.HEIGHT
            alpha = int(30 + 30 * math.sin(self._t + phase * 10))
            dot = pygame.Surface((2, 2), pygame.SRCALPHA)
            dot.fill((*cfg.COLOR_TEXT_DIM, max(0, alpha)))
            surface.blit(dot, (x, yy))

    def _draw_glow_text(self, surface, text, font, color, center, glow_color=None, glow_radius=3):
        glow_color = glow_color or color
        base = font.render(text, True, color)
        for dx in range(-glow_radius, glow_radius + 1):
            for dy in range(-glow_radius, glow_radius + 1):
                if dx == 0 and dy == 0:
                    continue
                if dx * dx + dy * dy > glow_radius * glow_radius:
                    continue
                ghost = font.render(text, True, glow_color)
                ghost.set_alpha(18)
                surface.blit(ghost, (center[0] - base.get_width() // 2 + dx,
                                      center[1] - base.get_height() // 2 + dy))
        surface.blit(base, (center[0] - base.get_width() // 2, center[1] - base.get_height() // 2))

    # ------------------------------------------------------------------
    def draw_menu(self, surface, selected_option=0, options=None):
        self._draw_background_texture(surface)
        surface.blit(self._menu_vignette, (0, 0))
        self._draw_scan_sweep(surface)

        # painel central em estilo "mira de câmera" — enquadra tudo
        panel = pygame.Rect(0, 0, 760, 760)
        panel.center = (cfg.WIDTH // 2, cfg.HEIGHT // 2 + 10)
        self._draw_viewfinder_panel(surface, panel)
        self._draw_rec_tag(surface, (panel.left + 26, panel.top + 24))

        cam_tag = self.font_small.render("MENU PRINCIPAL", True, cfg.COLOR_TEXT_DIM)
        surface.blit(cam_tag, (panel.right - cam_tag.get_width() - 22, panel.top + 18))

        self._draw_lens_icon(surface, (cfg.WIDTH // 2, panel.top + 90))

        pulse = 0.5 + 0.5 * math.sin(self._t * 1.3)
        title_color = tuple(int(cfg.COLOR_TEXT[k] + (cfg.COLOR_ACCENT[k] - cfg.COLOR_TEXT[k]) * 0.15 * pulse)
                             for k in range(3))
        title_y = panel.top + 175
        self._draw_glow_text(surface, "TURNO NOTURNO", self.font_title, title_color,
                              (cfg.WIDTH // 2, title_y), glow_color=cfg.COLOR_ACCENT, glow_radius=4)

        subtitle = self.font_medium.render("Centro de Observação Clínica", True, cfg.COLOR_ACCENT)
        subtitle_y = title_y + 50
        surface.blit(subtitle, (cfg.WIDTH // 2 - subtitle.get_width() // 2, subtitle_y))

        divider_y = subtitle_y + 42
        pygame.draw.line(surface, cfg.COLOR_CAM_BORDER,
                          (panel.centerx - 170, divider_y), (panel.centerx + 170, divider_y), 1)
        diamond = pygame.Rect(0, 0, 7, 7)
        diamond.center = (panel.centerx, divider_y)
        pygame.draw.rect(surface, cfg.COLOR_ACCENT, diamond)

        # options vem de game.py como lista de (action, label); aceitamos
        # também uma lista simples de strings pra manter compatibilidade.
        options = options or [("continue", "Iniciar turno"), ("quit", "Sair")]
        labels = [o[1] if isinstance(o, tuple) else o for o in options]

        option_w = 460
        option_h = 58
        option_gap = 18
        block_h = len(labels) * option_h + (len(labels) - 1) * option_gap
        avail_top = divider_y + 36
        avail_bottom = panel.bottom - 90
        start_y = avail_top + max(0, (avail_bottom - avail_top - block_h) // 2)

        for i, opt in enumerate(labels):
            active = i == selected_option
            bg = pygame.Rect(0, 0, option_w, option_h)
            bg.center = (cfg.WIDTH // 2, start_y + i * (option_h + option_gap) + option_h // 2)

            card = pygame.Surface((bg.width, bg.height), pygame.SRCALPHA)
            card.fill((*cfg.COLOR_PANEL_LIGHT, 130 if active else 70))
            surface.blit(card, bg.topleft)

            border_color = cfg.COLOR_ACCENT if active else cfg.COLOR_CAM_BORDER
            pygame.draw.rect(surface, border_color, bg, 1, border_radius=8)

            # barra de destaque à esquerda, "respira" quando selecionada
            accent_pulse = 0.5 + 0.5 * math.sin(self._t * 5.0)
            bar_w = 5 if not active else int(5 + 2 * accent_pulse)
            bar = pygame.Rect(bg.left, bg.top + 6, bar_w, bg.height - 12)
            pygame.draw.rect(surface, cfg.COLOR_ACCENT if active else cfg.COLOR_CAM_BORDER,
                              bar, border_radius=3)

            if active:
                glow = pygame.Surface((bg.width + 16, bg.height + 16), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*cfg.COLOR_ACCENT, int(30 + 25 * accent_pulse)),
                                  glow.get_rect(), border_radius=12)
                surface.blit(glow, (bg.left - 8, bg.top - 8), special_flags=pygame.BLEND_RGBA_ADD)

                slide = int(4 * accent_pulse)
                tri_x = bg.left + 26 + slide
                pygame.draw.polygon(surface, cfg.COLOR_ACCENT, [
                    (tri_x, bg.centery - 6), (tri_x, bg.centery + 6), (tri_x + 8, bg.centery)])

            color = cfg.COLOR_TEXT if active else cfg.COLOR_TEXT_DIM
            text_surf = self.font_medium.render(opt, True, color)
            text_x = bg.left + 52
            surface.blit(text_surf, (text_x, bg.centery - text_surf.get_height() // 2))

        hint = self.font_small.render("Setas para navegar, ENTER para confirmar", True, cfg.COLOR_TEXT_DIM)
        surface.blit(hint, (cfg.WIDTH // 2 - hint.get_width() // 2, panel.bottom - 46))

        surface.blit(self._menu_scanlines, (0, 0))

    # ------------------------------------------------------------------
    def draw_night_intro(self, surface, night_number):
        self._draw_background_texture(surface)
        surface.blit(self._menu_vignette, (0, 0))
        self._draw_scan_sweep(surface)

        pulse = 0.5 + 0.5 * math.sin(self._t * 1.5)
        color = tuple(int(cfg.COLOR_TEXT[k] + (cfg.COLOR_DANGER[k] - cfg.COLOR_TEXT[k]) * 0.2 * pulse)
                       for k in range(3))
        self._draw_glow_text(surface, f"NOITE {night_number}", self.font_large, color,
                              (cfg.WIDTH // 2, cfg.HEIGHT // 2 - 50), glow_color=cfg.COLOR_DANGER, glow_radius=3)

        if night_number > 1:
            flavor = self.font_small.render(
                "Os pacientes estão mais instáveis esta noite. Fique atento.",
                True, cfg.COLOR_TEXT_DIM)
            surface.blit(flavor, (cfg.WIDTH // 2 - flavor.get_width() // 2, cfg.HEIGHT // 2 - 12))

        hint = self.font_small.render("Pressione ENTER para começar", True, cfg.COLOR_TEXT_DIM)
        surface.blit(hint, (cfg.WIDTH // 2 - hint.get_width() // 2, cfg.HEIGHT // 2 + 10))
        surface.blit(self._menu_scanlines, (0, 0))

    # ------------------------------------------------------------------
    def draw_end_screen(self, surface, won, night_number, final_night):
        self._draw_background_texture(surface)
        surface.blit(self._menu_vignette, (0, 0))
        self._draw_scan_sweep(surface)
        if won:
            msg = "TURNO CONCLUÍDO"
            color = cfg.COLOR_ACCENT
            sub = "Ambos os pacientes permaneceram estáveis até o amanhecer."
        else:
            msg = "TURNO INTERROMPIDO"
            color = cfg.COLOR_DANGER
            sub = "A estabilidade de um paciente chegou a zero."

        self._draw_glow_text(surface, msg, self.font_large, color,
                              (cfg.WIDTH // 2, cfg.HEIGHT // 2 - 70), glow_color=color, glow_radius=4)
        sub_surf = self.font_small.render(sub, True, cfg.COLOR_TEXT_DIM)
        surface.blit(sub_surf, (cfg.WIDTH // 2 - sub_surf.get_width() // 2, cfg.HEIGHT // 2 - 20))

        if won and night_number < final_night:
            hint = "Pressione ENTER para seguir para a próxima noite"
        else:
            hint = "Pressione ENTER para voltar ao menu"
        hint_surf = self.font_small.render(hint, True, cfg.COLOR_TEXT)
        surface.blit(hint_surf, (cfg.WIDTH // 2 - hint_surf.get_width() // 2, cfg.HEIGHT // 2 + 30))
        surface.blit(self._menu_scanlines, (0, 0))
