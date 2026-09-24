"""Gera WAVs ausentes, sem dependências externas e sem sobrescrever a arte.

Uso opcional: python tools/generate_placeholder_audio.py
Os arquivos já estão incluídos no ZIP; isto NÃO roda ao iniciar o jogo.
"""

from array import array
from math import exp, pi, sin
from pathlib import Path
import random
import sys
import wave

SAMPLE_RATE = 22050
ASSETS = Path(__file__).resolve().parents[1] / "assets"


def tone(freqs, duration, amplitude=0.15, fade_speed=20):
    def sample(t):
        envelope = min(1, min(t, duration - t) * fade_speed)
        return sum(amplitude * sin(f * t * 2 * pi) for f in freqs) * envelope
    return sample


def hum_sample(t, rng):
    hum = 0.05 * sin(60 * t * 2 * pi) + 0.02 * sin(120 * t * 2 * pi)
    envelope = 0.72 + 0.18 * sin(t * 2 * pi / 6) + 0.10 * sin(t * pi)
    edge = max(0, min(1, t / 0.03, (6 - t) / 0.03))
    return (hum * envelope + rng.uniform(-0.01, 0.01)) * edge


def music_sample(t):
    vibrato = 1 + 0.004 * sin(0.11 * t * 2 * pi)
    sample = sum(0.055 * sin(f * vibrato * t * 2 * pi)
                 for f in (110, 146.83, 155.56))
    return sample * max(0, min(1, t / 2, (14 - t) / 2))


def knocks_sample(t):
    """Três batidas curtas usadas como pista sonora da história."""
    total = 0.0
    for onset in (0.1, 0.39, 0.68):
        local = t - onset
        if 0 <= local < 0.2:
            envelope = min(1, local * 700) * exp(-32 * local)
            total += envelope * (0.20 * sin(150 * local * 2 * pi)
                                 + 0.09 * sin(347 * local * 2 * pi))
    return total


def write_missing(path, duration, sample):
    if path.exists():
        return
    frames = array("h", (int(max(-1, min(1, sample(i / SAMPLE_RATE))) * 32767)
                         for i in range(int(SAMPLE_RATE * duration))))
    if sys.byteorder != "little":
        frames.byteswap()
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(frames.tobytes())
    print("Gerado:", path.name)


def main():
    tones = {
        "blip": ([440], 0.08, 0.25, 30),
        "alert": ([880], 0.25, 0.25, 30),
        "alert_soft": ([660], 0.15, 0.25, 30),
        "flicker": ([220], 0.12, 0.25, 30),
        "special": ([330, 392, 494], 0.4, 0.15, 20),
        "final_sting": ([220, 277, 330], 0.6, 0.15, 20),
        "protocol_success": ([392, 494, 587], 0.35, 0.15, 20),
        "danger": ([150], 0.3, 0.25, 30),
        "camera_switch": ([700], 0.05, 0.25, 30),
        "call_alert": ([523, 659], 0.18, 0.15, 20),
        "call_answered": ([440, 554, 659], 0.22, 0.15, 20),
        "call_expired": ([180], 0.35, 0.25, 30),
    }
    for name, (freqs, duration, amplitude, speed) in tones.items():
        write_missing(ASSETS / "sounds" / (name + ".wav"), duration,
                      tone(freqs, duration, amplitude, speed))
    rng = random.Random(1996)
    write_missing(ASSETS / "sounds/static_burst.wav", 0.35,
                  lambda t: rng.uniform(-0.2, 0.2))
    write_missing(ASSETS / "sounds/jumpscare.wav", 0.5,
                  lambda t: (rng.uniform(-0.55, 0.55) + 0.35 * sin(90 * t * 2 * pi))
                  * min(1, (0.5 - t) * 8))
    write_missing(ASSETS / "sounds/ambient_hum.wav", 6, lambda t: hum_sample(t, rng))
    write_missing(ASSETS / "music/ambient_music.wav", 14, music_sample)
    write_missing(ASSETS / "sounds/knocks.wav", 1.1, knocks_sample)


if __name__ == "__main__":
    main()
