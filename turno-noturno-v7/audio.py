"""
audio.py
Gerenciador de áudio. Tenta carregar arquivos reais de assets/sounds e
assets/music (para quando a arte final for adicionada); na ausência
deles, sintetiza pequenos efeitos sonoros simples (bipes/estática) via
numpy + pygame.sndarray. Se numpy não estiver disponível, opera em
modo silencioso sem quebrar o jogo.

Isso permite trocar os placeholders por sons reais depois sem alterar
nenhuma outra parte do código: basta colocar os arquivos com os nomes
esperados dentro de assets/sounds/.
"""

import os
import pygame
import settings as cfg

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False

ASSETS_SOUND_DIR = os.path.join(os.path.dirname(__file__), "assets", "sounds")
ASSETS_MUSIC_DIR = os.path.join(os.path.dirname(__file__), "assets", "music")

SAMPLE_RATE = 22050


class AudioManager:
    def __init__(self):
        self.enabled = True
        try:
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
            # Reserva 2 canais fixos pro loop ambiente (zumbido/flicker) e
            # pra música baixinha de fundo, pra eles não serem roubados
            # pelo play() automático dos efeitos pontuais (blip, alert etc).
            pygame.mixer.set_num_channels(16)
            pygame.mixer.set_reserved(2)
            self._hum_channel = pygame.mixer.Channel(0)
            self._music_channel = pygame.mixer.Channel(1)
        except pygame.error as e:
            self.enabled = False
            self._hum_channel = None
            self._music_channel = None
            print(f"[audio] AVISO: pygame.mixer não inicializou ({e}). "
                  f"O jogo vai rodar sem som nenhum. Verifique se o sistema "
                  f"tem uma saída de áudio disponível.")

        if self.enabled and not _HAS_NUMPY:
            print("[audio] AVISO: numpy não está instalado, então os sons "
                  "sintetizados (placeholder) não vão tocar. Rode "
                  "'pip install numpy' OU coloque arquivos .wav reais em "
                  "assets/sounds/ (eles não precisam de numpy).")

        self.sounds = {}
        if self.enabled:
            self._load_or_synthesize()
            loaded = sum(1 for s in self.sounds.values() if s is not None)
            print(f"[audio] {loaded}/{len(self.sounds)} efeitos sonoros prontos.")

    # ------------------------------------------------------------------
    def _load_or_synthesize(self):
        # nome_logico: (arquivo_esperado, gerador_sintetico)
        specs = {
            "blip": ("blip.wav", lambda: self._tone(440, 0.08)),
            "alert": ("alert.wav", lambda: self._tone(880, 0.25)),
            "alert_soft": ("alert_soft.wav", lambda: self._tone(660, 0.15)),
            "static_burst": ("static_burst.wav", lambda: self._noise(0.35)),
            "flicker": ("flicker.wav", lambda: self._tone(220, 0.12)),
            "special": ("special.wav", lambda: self._chord([330, 392, 494], 0.4)),
            "final_sting": ("final_sting.wav", lambda: self._chord([220, 277, 330], 0.6)),
            "protocol_success": ("protocol_success.wav", lambda: self._chord([392, 494, 587], 0.35)),
            "danger": ("danger.wav", lambda: self._tone(150, 0.3)),
            "jumpscare": ("jumpscare.wav", lambda: self._jumpscare_noise(0.5)),
            "camera_switch": ("camera_switch.wav", lambda: self._tone(700, 0.05)),
            "call_alert": ("call_alert.wav", lambda: self._chord([523, 659], 0.18)),
            "call_answered": ("call_answered.wav", lambda: self._chord([440, 554, 659], 0.22)),
            "call_expired": ("call_expired.wav", lambda: self._tone(180, 0.35)),
            # Loops de atmosfera (tocam continuamente durante a noite, ver
            # start_ambient/stop_ambient) — nomes de arquivo esperados em
            # assets/sounds/ e assets/music/ respectivamente, se quiser
            # trocar pelos sons reais depois.
            "ambient_hum": ("ambient_hum.wav", lambda: self._hum_loop(6.0)),
            "ambient_music": ("ambient_music.wav", lambda: self._music_pad(14.0)),
        }
        for key, (filename, synth) in specs.items():
            # "ambient_music" é o único que procura em assets/music/ primeiro
            # (aceita .wav, .ogg ou .mp3 lá) — os demais ficam em assets/sounds/.
            if key == "ambient_music":
                path = self._find_music_file(filename)
            else:
                path = os.path.join(ASSETS_SOUND_DIR, filename)
            if path and os.path.isfile(path):
                try:
                    self.sounds[key] = pygame.mixer.Sound(path)
                    continue
                except pygame.error as e:
                    print(f"[audio] AVISO: não consegui carregar {filename} ({e}). "
                          f"Verifique se o arquivo é um .wav válido.")
            if _HAS_NUMPY:
                try:
                    self.sounds[key] = synth()
                except Exception:
                    self.sounds[key] = None
            else:
                self.sounds[key] = None

    # ------------------------------------------------------------------
    def _find_music_file(self, default_filename):
        """Procura a música ambiente em assets/music/, aceitando .wav ou
        .ogg (pygame.mixer.Sound não lê .mp3 de forma confiável em todo
        sistema, então .mp3 fica de fora por segurança)."""
        stem = os.path.splitext(default_filename)[0]
        for ext in (".wav", ".ogg"):
            candidate = os.path.join(ASSETS_MUSIC_DIR, stem + ext)
            if os.path.isfile(candidate):
                return candidate
        return None

    # ------------------------------------------------------------------
    def _tone(self, freq, duration):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        wave = 0.25 * np.sin(freq * t * 2 * np.pi)
        fade = np.minimum(1, np.minimum(t, duration - t) * 30)
        wave = wave * fade
        audio = (wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(audio)

    def _chord(self, freqs, duration):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        wave = sum(0.15 * np.sin(f * t * 2 * np.pi) for f in freqs)
        fade = np.minimum(1, np.minimum(t, duration - t) * 20)
        wave = wave * fade
        audio = (wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(audio)

    def _noise(self, duration):
        samples = int(SAMPLE_RATE * duration)
        wave = (np.random.rand(samples) * 2 - 1) * 0.2
        audio = (wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(audio)

    def _jumpscare_noise(self, duration):
        # ataque abrupto (sem fade-in) + ruído distorcido + tom grave —
        # o "abrupto" é o que faz parecer um susto e não um efeito suave.
        samples = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, samples, False)
        noise = (np.random.rand(samples) * 2 - 1) * 0.55
        low_tone = 0.35 * np.sin(90 * t * 2 * np.pi)
        wave = noise + low_tone
        fade_out = np.minimum(1, (duration - t) * 8)  # sem fade-in, só sai suave no final
        wave = wave * fade_out
        wave = np.clip(wave, -1, 1)
        audio = (wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(audio)

    def _hum_loop(self, duration):
        """Zumbido elétrico contínuo com uma leve modulação de amplitude
        simulando lâmpada fluorescente instável ('luz piscando' em loop,
        clima backrooms) — pensado pra tocar em loops=-1 sem parar."""
        n = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, n, False)
        hum = 0.05 * np.sin(60 * t * 2 * np.pi)
        hum += 0.02 * np.sin(120 * t * 2 * np.pi)  # harmônico do zumbido
        # envelope de "piscar" lento e irregular, mas periódico dentro da
        # duração do loop pra não estalar na costura
        flicker_env = (0.72 + 0.18 * np.sin(t * 2 * np.pi * (1 / duration))
                       + 0.10 * np.sin(t * 2 * np.pi * (3 / duration)))
        noise_floor = (np.random.rand(n) * 2 - 1) * 0.010
        wave = hum * flicker_env + noise_floor
        # fade bem curto nas pontas só pra evitar clique na costura do loop
        edge = int(SAMPLE_RATE * 0.03)
        fade = np.ones(n)
        fade[:edge] = np.linspace(0, 1, edge)
        fade[-edge:] = np.linspace(1, 0, edge)
        wave = np.clip(wave * fade, -1, 1)
        audio = (wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(audio)

    def _music_pad(self, duration):
        """Pad ambiente bem baixinho, um acorde suspenso/dissonante que
        respira devagar — só pra dar clima de fundo, nunca protagonismo.
        Começa e termina em silêncio (fade), então o loop=-1 encaixa sem
        clique nenhum na costura."""
        n = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, n, False)
        freqs = [110.0, 146.83, 155.56]  # A2, D3, D#3 — tenso mas contido
        wave = np.zeros(n)
        for f in freqs:
            vibrato = 1.0 + 0.004 * np.sin(0.11 * t * 2 * np.pi)
            wave += 0.055 * np.sin(f * vibrato * t * 2 * np.pi)
        fade_len = int(SAMPLE_RATE * 2.0)
        fade = np.ones(n)
        fade[:fade_len] = np.linspace(0, 1, fade_len)
        fade[-fade_len:] = np.linspace(1, 0, fade_len)
        wave = np.clip(wave * fade, -1, 1)
        audio = (wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(audio)

    # ------------------------------------------------------------------
    def _play(self, key):
        if not self.enabled:
            return
        snd = self.sounds.get(key)
        if snd is not None:
            snd.set_volume(cfg.MASTER_VOLUME)
            snd.play()

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

    def play_final_sting(self):
        self._play("final_sting")

    def play_protocol_success(self):
        self._play("protocol_success")

    def play_danger(self):
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

    # ------------------------------------------------------------------
    def start_ambient(self):
        """Liga o zumbido/flicker ambiente e a música de fundo em loop
        infinito, cada um no seu canal reservado. Chamado ao começar a
        noite; idempotente (não reinicia se já estiver tocando)."""
        if not self.enabled:
            return
        hum = self.sounds.get("ambient_hum")
        if hum is not None and self._hum_channel is not None and not self._hum_channel.get_busy():
            self._hum_channel.set_volume(cfg.AMBIENT_HUM_VOLUME * cfg.MASTER_VOLUME)
            self._hum_channel.play(hum, loops=-1)
        music = self.sounds.get("ambient_music")
        if music is not None and self._music_channel is not None and not self._music_channel.get_busy():
            self._music_channel.set_volume(cfg.AMBIENT_MUSIC_VOLUME * cfg.MASTER_VOLUME)
            self._music_channel.play(music, loops=-1)

    def stop_ambient(self):
        """Desliga os dois loops de atmosfera (fim de noite / volta ao menu)."""
        if not self.enabled:
            return
        if self._hum_channel is not None:
            self._hum_channel.stop()
        if self._music_channel is not None:
            self._music_channel.stop()
