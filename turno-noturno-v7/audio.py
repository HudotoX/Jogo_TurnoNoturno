"""Áudio por arquivos WAV/OGG: apenas Pygame, sem síntese em runtime.

Os sons de teste já acompanham o projeto em assets/. Para trocar a arte,
substitua os arquivos mantendo os nomes. O gerador opcional em tools/
recria placeholders ausentes usando apenas a biblioteca padrão do Python.
"""

import os

import pygame
import settings as cfg

ASSETS_SOUND_DIR = os.path.join(os.path.dirname(__file__), "assets", "sounds")
ASSETS_MUSIC_DIR = os.path.join(os.path.dirname(__file__), "assets", "music")
SAMPLE_RATE = 22050
SOUND_NAMES = (
    "blip", "alert", "alert_soft", "static_burst", "flicker", "special",
    "final_sting", "protocol_success", "danger", "jumpscare", "camera_switch",
    "call_alert", "call_answered", "call_expired", "ambient_hum", "ambient_music", "knocks",
)


class AudioManager:
    def __init__(self):
        self.enabled = True
        self.sounds = {}
        self._hum_channel = None
        self._music_channel = None
        self._last_danger_ms = -10000
        try:
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
            pygame.mixer.set_num_channels(16)
            pygame.mixer.set_reserved(2)
            self._hum_channel = pygame.mixer.Channel(0)
            self._music_channel = pygame.mixer.Channel(1)
        except pygame.error as exc:
            self.enabled = False
            print(f"[audio] Sem saída de áudio ({exc}). O jogo continuará sem som.")

        if self.enabled:
            self._load_sounds()
            loaded = sum(sound is not None for sound in self.sounds.values())
            print(f"[audio] {loaded}/{len(SOUND_NAMES)} efeitos sonoros prontos.")

    def _load_sounds(self):
        for name in SOUND_NAMES:
            filename = name + ".wav"
            path = (self._find_music_file(filename) if name == "ambient_music"
                    else os.path.join(ASSETS_SOUND_DIR, filename))
            self.sounds[name] = None
            if not path or not os.path.isfile(path):
                print(f"[audio] Arquivo ausente: {filename}. Copie a pasta assets completa.")
                continue
            try:
                self.sounds[name] = pygame.mixer.Sound(path)
            except (pygame.error, OSError) as exc:
                print(f"[audio] Não consegui carregar {filename}: {exc}")

    def _find_music_file(self, filename):
        stem = os.path.splitext(filename)[0]
        for ext in (".wav", ".ogg"):
            path = os.path.join(ASSETS_MUSIC_DIR, stem + ext)
            if os.path.isfile(path):
                return path
        return None

    def _play(self, key):
        if not self.enabled:
            return
        sound = self.sounds.get(key)
        if sound is not None:
            sound.set_volume(cfg.MASTER_VOLUME)
            sound.play()

    def play_blip(self):
        self._play("blip")

    def play_alert(self):
        self._play("alert")

    def play_alert_soft(self):
        self._play("alert_soft")

    def play_static_burst(self):
        self._play("static_burst")

    def play_flicker(self):
        self._play("flicker")

    def play_special(self):
        self._play("special")

    def play_knocks(self):
        self._play("knocks")

    def play_final_sting(self):
        self._play("final_sting")

    def play_protocol_success(self):
        self._play("protocol_success")

    def play_danger(self):
        now = pygame.time.get_ticks()
        if now - self._last_danger_ms >= 1200:
            self._last_danger_ms = now
            self._play("danger")

    def play_jumpscare(self):
        self._play("jumpscare")

    def play_camera_switch(self):
        self._play("camera_switch")

    def play_call_alert(self):
        self._play("call_alert")

    def play_call_answered(self):
        self._play("call_answered")

    def play_call_expired(self):
        self._play("call_expired")

    def start_ambient(self):
        if not self.enabled:
            return
        hum = self.sounds.get("ambient_hum")
        if hum is not None and not self._hum_channel.get_busy():
            self._hum_channel.set_volume(cfg.AMBIENT_HUM_VOLUME * cfg.MASTER_VOLUME)
            self._hum_channel.play(hum, loops=-1)
        music = self.sounds.get("ambient_music")
        if music is not None and not self._music_channel.get_busy():
            self._music_channel.set_volume(cfg.AMBIENT_MUSIC_VOLUME * cfg.MASTER_VOLUME)
            self._music_channel.play(music, loops=-1)

    def stop_ambient(self):
        if not self.enabled:
            return
        self._hum_channel.stop()
        self._music_channel.stop()
