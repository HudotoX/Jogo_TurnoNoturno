"""
camera_system.py
Gerencia a câmera ativa e desenha o feed placeholder de cada sala,
incluindo os pacientes presentes nela, com uma estética de CRT
(scanlines, leve vinheta, brilho).

Suporte a assets reais: se existirem imagens em
  assets/backgrounds/<chave-da-sala>.png   (bed, hall, desk, yard)
  assets/sprites/patient_<id>.png          (patient_01, patient_02)
elas são carregadas e usadas no lugar do desenho geométrico
automaticamente — não é preciso alterar nenhum código para trocar a
arte, só colocar os arquivos com esses nomes nas pastas.
"""

import math
import os
import random
import pygame
import settings as cfg
from ui import load_font

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
BACKGROUNDS_DIR = os.path.join(ASSETS_DIR, "backgrounds")
SPRITES_DIR = os.path.join(ASSETS_DIR, "sprites")


class CameraSystem:
    def __init__(self, switch_cooldown_mult=1.0):
        self.cameras = list(cfg.CAMERAS)
        # aplica a dificuldade da noite (ver settings.NIGHT_DIFFICULTY) à
        # fricção de troca de câmera — noites mais tarde punem mais o
        # "pingue-pongue" entre câmeras.
        self._switch_cooldown_base = cfg.CAMERA_SWITCH_COOLDOWN * switch_cooldown_mult
        self.active_index = 0
        self.interference_timer = 0.0
        self.interference_cam = None
        self.switch_cooldown = 0.0
        self.blackout_timer = 0.0
        self._time = 0.0

        self._anchor_seed = {cam: random.Random(i) for i, cam in enumerate(self.cameras)}
        self._patient_spot_cache = {}  # (patient_id, room) -> frac_x, fixo até o paciente mudar de sala
        # elementos de cenário fixos por sala (silhuetas simples: cama, mesa, janela)
        self._room_props = {
            self.cameras[0]: "bed",
            self.cameras[1]: "hall",
            self.cameras[2]: "desk",
            self.cameras[3]: "yard",
        }
        self._label_font = load_font(15)
        self._rec_font = load_font(14, bold=True)

        self.bg_images = self._load_backgrounds()
        self.patient_images = self._load_patient_sprites()

    # ------------------------------------------------------------------
    def _load_backgrounds(self):
        images = {}
        for prop_key in set(self._room_props.values()):
            path = os.path.join(BACKGROUNDS_DIR, f"{prop_key}.png")
            if os.path.isfile(path):
                try:
                    images[prop_key] = pygame.image.load(path).convert()
                except pygame.error:
                    pass
        return images

    def _load_patient_sprites(self):
        images = {}
        for patient_id in (1, 2):
            path = os.path.join(SPRITES_DIR, f"patient_{patient_id:02d}.png")
            if os.path.isfile(path):
                try:
                    images[patient_id] = pygame.image.load(path).convert_alpha()
                except pygame.error:
                    pass
        return images

    @property
    def active_camera(self):
        return self.cameras[self.active_index]

    def switch_to(self, index):
        if self.switch_cooldown > 0:
            return False
        if 0 <= index < len(self.cameras) and index != self.active_index:
            self.active_index = index
            self.switch_cooldown = self._switch_cooldown_base
            return True
        return False

    def next_camera(self):
        return self.switch_to((self.active_index + 1) % len(self.cameras))

    def prev_camera(self):
        return self.switch_to((self.active_index - 1) % len(self.cameras))

    def trigger_interference(self, duration=1.6, cam=None):
        self.interference_cam = cam or self.active_camera
        self.interference_timer = duration

    def trigger_blackout(self, duration=None):
        self.blackout_timer = duration if duration is not None else cfg.BLACKOUT_DURATION

    @property
    def is_blackout(self):
        return self.blackout_timer > 0

    def update(self, dt):
        self._time += dt
        self.switch_cooldown = max(0.0, self.switch_cooldown - dt)
        self.blackout_timer = max(0.0, self.blackout_timer - dt)
        if self.interference_timer > 0:
            self.interference_timer = max(0.0, self.interference_timer - dt)
            if self.interference_timer == 0:
                self.interference_cam = None

    # ------------------------------------------------------------------
    def draw_feed(self, surface, rect, cam_name, patients, font, flicker=False):
        pygame.draw.rect(surface, (6, 7, 10), rect)

        # tudo daqui pra baixo fica travado dentro do retângulo da câmera —
        # sem isso, sprite grande/paciente perto da borda vazava por cima do
        # frame, do border e do HUD, e ficava "flutuando" desconexo da cena.
        prev_clip = surface.get_clip()
        surface.set_clip(rect)
        try:
            if self.is_blackout:
                self._draw_blackout(surface, rect, font)
                return

            if flicker and random.random() < 0.5:
                pygame.draw.rect(surface, (3, 3, 4), rect)
                self._draw_border(surface, rect, active=True)
                self._draw_hud_corner_marks(surface, rect, cam_name)
                return

            self._draw_room_backdrop(surface, rect, cam_name)

            for p in patients:
                if p.room != cam_name or p.is_hidden:
                    continue
                self._draw_patient_marker(surface, rect, cam_name, p, font)

            if self.interference_cam == cam_name and self.interference_timer > 0:
                self._draw_static(surface, rect)

            # escurecida uniforme por cima de cenário + pacientes, ANTES do
            # filtro de scanline/vinheta — é isso que faz o paciente parecer
            # "gravado pela câmera" junto com o resto, e não colado em cima.
            self._draw_signal_dim(surface, rect)

            # filtro verde/CRT (respiração ambiente) — agora por cima de TUDO
            # (cenário + paciente), não só do fundo, senão o paciente ficava
            # sem o tingimento e destoava do resto da imagem.
            self._draw_ambient_glow(surface, rect, cam_name)

            self._draw_scanlines(surface, rect)
            self._draw_vignette(surface, rect)
            self._draw_border(surface, rect, active=True)
            self._draw_hud_corner_marks(surface, rect, cam_name)
        finally:
            surface.set_clip(prev_clip)

    # ------------------------------------------------------------------
    def _draw_room_backdrop(self, surface, rect, cam_name):
        prop = self._room_props.get(cam_name, "hall")
        bg_image = self.bg_images.get(prop)

        if bg_image is not None:
            scaled = pygame.transform.smoothscale(bg_image, (rect.width, rect.height))
            surface.blit(scaled, rect.topleft)
        else:
            self._draw_procedural_backdrop(surface, rect, prop)

    def _draw_procedural_backdrop(self, surface, rect, prop):
        # gradiente vertical sutil simulando iluminação de teto
        top_c = (20, 23, 29)
        bot_c = (10, 11, 15)
        steps = 24
        for i in range(steps):
            t = i / steps
            color = tuple(int(top_c[k] + (bot_c[k] - top_c[k]) * t) for k in range(3))
            y = rect.top + int(rect.height * t)
            h = max(1, rect.height // steps + 1)
            pygame.draw.rect(surface, color, (rect.left, y, rect.width, h))

        # grade de parede
        for i in range(6):
            x = rect.left + (i + 1) * rect.width // 7
            pygame.draw.line(surface, (26, 29, 36), (x, rect.top), (x, rect.bottom), 1)
        floor_y = rect.bottom - int(rect.height * 0.22)
        pygame.draw.line(surface, (32, 36, 44), (rect.left, floor_y), (rect.right, floor_y), 2)

        if prop == "bed":
            r = pygame.Rect(rect.left + 24, floor_y - 26, 110, 30)
            pygame.draw.rect(surface, (40, 46, 56), r, border_radius=4)
            pygame.draw.rect(surface, (30, 34, 42), r, 2, border_radius=4)
        elif prop == "desk":
            r = pygame.Rect(rect.right - 150, floor_y - 34, 120, 34)
            pygame.draw.rect(surface, (38, 44, 54), r, border_radius=3)
            pygame.draw.rect(surface, (30, 34, 42), r, 2, border_radius=3)
        elif prop == "yard":
            for wx in range(rect.left + 40, rect.right - 20, 90):
                pygame.draw.line(surface, (34, 46, 44), (wx, rect.top + 30), (wx, floor_y), 3)
        # "hall" fica só com a grade mesmo — corredor vazio

    # ------------------------------------------------------------------
    def _floor_y(self, rect):
        """Mesma linha de 'chão' usada no cenário procedural — ancora o
        paciente nela pra ele ficar de pé na sala, não flutuando."""
        return rect.bottom - int(rect.height * 0.22)

    def _get_patient_spot(self, patient_id, cam_name, rect):
        """Posição estável do paciente dentro da sala — só muda quando ele
        realmente troca de sala (nunca a cada frame), pra não 'pipocar'."""
        key = (patient_id, cam_name)
        if key not in self._patient_spot_cache:
            rng = self._anchor_seed[cam_name]
            frac_x = rng.uniform(0.20, 0.80)
            self._patient_spot_cache[key] = frac_x
        frac_x = self._patient_spot_cache[key]
        px = rect.left + int(rect.width * frac_x)

        prop = self._room_props.get(cam_name, "hall")
        offset = cfg.PATIENT_ROOM_Y_OFFSET.get(prop, 0)
        py = self._floor_y(rect) + offset
        # trava dentro do quadro — não deixa o offset jogar o boneco pra
        # fora da câmera (nem em cima do teto, nem embaixo do chão).
        py = max(rect.top + 40, min(py, rect.bottom - 4))
        return px, py

    def _patient_target_height(self, cam_name, rect, foot_y):
        prop = self._room_props.get(cam_name, "hall")
        scale = cfg.PATIENT_ROOM_SCALE.get(prop, 1.0)
        desired = int(cfg.PATIENT_SPRITE_BASE_HEIGHT * scale)
        # nunca deixa o sprite passar do topo do quadro da câmera — se a
        # altura configurada não cabe entre o teto e o pé do boneco (já
        # considerando o offset vertical), encolhe até caber, em vez de
        # cortar a cabeça.
        available = foot_y - rect.top - 12
        return max(40, min(desired, available))

    def _draw_patient_marker(self, surface, rect, cam_name, p, font):
        px, foot_y = self._get_patient_spot(p.id, cam_name, rect)
        color = cfg.STATE_COLORS.get(p.state, cfg.COLOR_TEXT)

        # sprite original olha pra ESQUERDA. Se o paciente está na metade
        # esquerda da tela, flipa (passa a olhar pra direita); se está na
        # metade direita, mantém — assim ele sempre "olha" pro centro do
        # quadro em vez de de costas pra cena.
        facing_left = (px - rect.left) >= rect.width / 2
        flip_x = not facing_left

        sprite = self.patient_images.get(p.id)
        target_h = self._patient_target_height(cam_name, rect, foot_y) if sprite is not None else 120
        body_top = foot_y - target_h
        mid_y = body_top + target_h // 3  # altura aproximada do "peito/cabeça" pra glow e tag

        pulse = 0.5 + 0.5 * math.sin(self._time * 4.0)
        base_radius = 13

        if p.is_glitched:
            for k in range(2):
                offset_x = random.randint(-8, 8)
                offset_y = random.randint(-3, 3)
                ghost = pygame.Surface((60, 60), pygame.SRCALPHA)
                pygame.draw.circle(ghost, (*color, 60), (30, 30), base_radius + 6)
                surface.blit(ghost, (px + offset_x - 30, mid_y + offset_y - 30))

        glow_r = int(base_radius + 10 + 6 * pulse) if p.state in ("ANORMAL", "PERIGO") else base_radius + 6
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, 70), (glow_r, glow_r), glow_r)
        surface.blit(glow, (px - glow_r, mid_y - glow_r), special_flags=pygame.BLEND_RGBA_ADD)

        if sprite is not None:
            self._draw_patient_sprite(surface, sprite, px, foot_y, target_h, color, p.state, flip_x)
        else:
            # corpo simplificado: cabeça + "ombros" (silhueta minimalista)
            pygame.draw.circle(surface, color, (px, mid_y), base_radius)
            pygame.draw.circle(surface, (5, 5, 6), (px, mid_y), base_radius, 2)
            shoulders = pygame.Rect(px - 20, mid_y + base_radius - 2, 40, 16)
            pygame.draw.ellipse(surface, color, shoulders)
            pygame.draw.ellipse(surface, (5, 5, 6), shoulders, 2)

        label = font.render(p.name.split()[0], True, cfg.COLOR_TEXT)
        tag_bg = pygame.Rect(px - label.get_width() // 2 - 4, body_top - 26, label.get_width() + 8, 16)
        tag_surf = pygame.Surface((tag_bg.width, tag_bg.height), pygame.SRCALPHA)
        tag_surf.fill((0, 0, 0, 130))
        surface.blit(tag_surf, tag_bg.topleft)
        surface.blit(label, (tag_bg.left + 4, tag_bg.top + 1))

    def _draw_patient_sprite(self, surface, sprite, px, foot_y, target_h, state_color, state, flip_x):
        # sprite é ancorado pelos "pés": px, foot_y fica no chão do personagem
        w, h = sprite.get_size()
        scale = target_h / h
        scaled = pygame.transform.smoothscale(sprite, (max(1, int(w * scale)), target_h))
        if flip_x:
            scaled = pygame.transform.flip(scaled, True, False)
        dest = scaled.get_rect(midbottom=(px, foot_y))
        surface.blit(scaled, dest)

        # tingimento sutil pela cor do estado, só quando não está NORMAL
        if state != "NORMAL":
            tint = pygame.Surface(scaled.get_size(), pygame.SRCALPHA)
            tint.fill((*state_color, 60))
            tint.blit(scaled, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(tint, dest.topleft, special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_signal_dim(self, surface, rect):
        dim = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, cfg.SIGNAL_DIM_ALPHA))
        surface.blit(dim, rect.topleft)

    def _draw_ambient_glow(self, surface, rect, cam_name):
        """Tingimento verde/CRT que 'respira' bem devagar — cobre cenário
        e pacientes igual, então os dois pegam o mesmo filtro de câmera."""
        pulse = 0.5 + 0.5 * math.sin(self._time * 0.6 + hash(cam_name) % 10)
        glow_alpha = int(10 + 14 * pulse)
        glow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        glow.fill((*cfg.CRT_GLOW_COLOR, glow_alpha))
        surface.blit(glow, rect.topleft, special_flags=pygame.BLEND_RGBA_ADD)

    # ------------------------------------------------------------------
    def _draw_scanlines(self, surface, rect):
        line_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        y = 0
        while y < rect.height:
            pygame.draw.line(line_surf, (0, 0, 0, cfg.SCANLINE_ALPHA), (0, y), (rect.width, y))
            y += cfg.SCANLINE_SPACING
        surface.blit(line_surf, rect.topleft)

    def _draw_vignette(self, surface, rect):
        vig = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        border = 26
        pygame.draw.rect(vig, (0, 0, 0, 130), (0, 0, rect.width, border))
        pygame.draw.rect(vig, (0, 0, 0, 130), (0, rect.height - border, rect.width, border))
        pygame.draw.rect(vig, (0, 0, 0, 110), (0, 0, border, rect.height))
        pygame.draw.rect(vig, (0, 0, 0, 110), (rect.width - border, 0, border, rect.height))
        surface.blit(vig, rect.topleft)

    def _draw_border(self, surface, rect, active=True):
        color = cfg.COLOR_CAM_BORDER_ACTIVE if active else cfg.COLOR_CAM_BORDER
        pygame.draw.rect(surface, color, rect, 2)
        # cantos reforçados, estilo viewfinder
        c = 16
        for corner in [(rect.left, rect.top, 1, 1), (rect.right, rect.top, -1, 1),
                       (rect.left, rect.bottom, 1, -1), (rect.right, rect.bottom, -1, -1)]:
            x, y, dx, dy = corner
            pygame.draw.line(surface, color, (x, y), (x + c * dx, y), 3)
            pygame.draw.line(surface, color, (x, y), (x, y + c * dy), 3)

    def _draw_hud_corner_marks(self, surface, rect, cam_name):
        label = self._label_font.render(f"{cam_name} — {cfg.ROOM_LABELS.get(cam_name, '')}", True, cfg.COLOR_TEXT_DIM)
        tag_bg = pygame.Surface((label.get_width() + 12, label.get_height() + 8), pygame.SRCALPHA)
        tag_bg.fill((0, 0, 0, 140))
        surface.blit(tag_bg, (rect.left + 6, rect.top + 6))
        surface.blit(label, (rect.left + 12, rect.top + 10))

        # indicador REC piscando
        blink = int(self._time * 2) % 2 == 0
        if blink:
            rec_color = (220, 70, 70)
            pygame.draw.circle(surface, rec_color, (rect.right - 60, rect.top + 18), 5)
        rec_label = self._rec_font.render("REC", True, (220, 70, 70))
        surface.blit(rec_label, (rect.right - 48, rect.top + 11))

    def _draw_static(self, surface, rect):
        static_surf = pygame.Surface((rect.width, rect.height))
        for _ in range(260):
            x = random.randint(0, rect.width - 1)
            y = random.randint(0, rect.height - 1)
            shade = random.randint(40, 210)
            static_surf.set_at((x, y), (shade, shade, shade))
        surface.blit(static_surf, rect.topleft, special_flags=pygame.BLEND_ADD)

    def _draw_blackout(self, surface, rect, font):
        pygame.draw.rect(surface, (0, 0, 0), rect)
        # estática esparsa bem fraca, pra não ficar 100% morto visualmente
        for _ in range(40):
            x = random.randint(rect.left, rect.right - 1)
            y = random.randint(rect.top, rect.bottom - 1)
            shade = random.randint(10, 45)
            pygame.draw.circle(surface, (shade, shade, shade), (x, y), 1)

        label = font.render("SEM SINAL", True, (140, 40, 40))
        surface.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))
        self._draw_border(surface, rect, active=True)
