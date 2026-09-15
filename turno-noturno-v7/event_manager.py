"""
event_manager.py
Dispara os eventos roteirizados de cada noite (ver nights.py) no
momento correto do relógio in-game e aplica seus efeitos ao mundo
(pacientes, câmeras, áudio, log da UI).

Não há IA complexa aqui: apenas comparação de timers contra uma
lista de eventos ordenada por tempo.
"""

import random
from nights import NIGHT_EVENTS, EVENT_LOG_TEXT
import settings as cfg


class EventManager:
    def __init__(self, night_number):
        self.events = sorted(NIGHT_EVENTS.get(night_number, []), key=lambda e: e["time"])
        self._next_index = 0
        self.log_messages = []  # (texto, tempo_de_exibicao_restante)
        self.final_event_triggered = False

    # ------------------------------------------------------------------
    def game_minutes_elapsed(self, night_elapsed_seconds):
        """Converte segundos reais decorridos em 'minutos in-game' (0-360)."""
        progress = night_elapsed_seconds / cfg.NIGHT_DURATION_SECONDS
        return progress * 360.0

    # ------------------------------------------------------------------
    def update(self, dt, night_elapsed_seconds, patients, camera_system, audio):
        current_minutes = self.game_minutes_elapsed(night_elapsed_seconds)

        while self._next_index < len(self.events) and self.events[self._next_index]["time"] <= current_minutes:
            event = self.events[self._next_index]
            self._execute(event, patients, camera_system, audio)
            self._next_index += 1

        # atualizar timers de mensagens de log
        self.log_messages = [(txt, t - dt) for (txt, t) in self.log_messages if t - dt > 0]

    # ------------------------------------------------------------------
    def _execute(self, event, patients, camera_system, audio):
        etype = event["type"]
        payload = event.get("payload", {})

        if etype == "light_flicker":
            audio.play_flicker()
            self._flicker_hold = 1.2

        elif etype == "patient_move":
            pid = payload.get("patient_id")
            patient = self._find_patient(patients, pid)
            if patient:
                patient.move_to_random_room(camera_system.cameras)
                audio.play_blip()

        elif etype == "camera_interference":
            cam = random.choice(camera_system.cameras)
            camera_system.trigger_interference(duration=2.0, cam=cam)
            audio.play_static_burst()

        elif etype == "anomaly_sighting":
            pid = payload.get("patient_id")
            patient = self._find_patient(patients, pid)
            if patient:
                patient.trigger_glitch(duration=7.0)
                patient.trigger_crisis(multiplier=1.6, duration=10.0)
                audio.play_alert_soft()

        elif etype == "false_alarm":
            # visual e som IDÊNTICOS ao anomaly_sighting, mas sem acelerar o
            # decaimento — só um custo pequeno e pontual. É assim que fica
            # indistinguível de um alarme real sem olhar a barra de verdade.
            pid = payload.get("patient_id")
            patient = self._find_patient(patients, pid)
            if patient:
                patient.trigger_glitch(duration=5.0)
                patient.stability = max(0.0, patient.stability - cfg.FALSE_ALARM_STABILITY_COST)
                patient._recompute_state()
                audio.play_alert_soft()

        elif etype == "patient_call":
            pid = payload.get("patient_id")
            patient = self._find_patient(patients, pid)
            if patient:
                patient.start_call(scripted=True)
                audio.play_call_alert()

        elif etype == "patient_disappear":
            pid = payload.get("patient_id")
            patient = self._find_patient(patients, pid)
            if patient:
                patient.is_hidden = True
                patient._hidden_timer = 14.0
                audio.play_alert()

        elif etype == "blackout":
            camera_system.trigger_blackout(cfg.BLACKOUT_DURATION)
            audio.play_static_burst()

        elif etype == "jumpscare_event":
            self._jumpscare_flag = True

        elif etype == "special_event":
            audio.play_special()

        elif etype == "final_event":
            self.final_event_triggered = True
            audio.play_final_sting()

        text = EVENT_LOG_TEXT.get(etype, "")
        if text:
            self.log_messages.append([text, 6.0])

    @staticmethod
    def _find_patient(patients, pid):
        for p in patients:
            if p.id == pid:
                return p
        return None

    # ------------------------------------------------------------------
    def consume_flicker_flag(self):
        """Usado pela UI/câmera para saber se deve desenhar o piscar de luz."""
        flag = getattr(self, "_flicker_hold", 0.0)
        if flag > 0:
            self._flicker_hold = max(0.0, flag - 1 / cfg.FPS)
            return True
        return False

    def consume_jumpscare_flag(self):
        """Usado pelo game.py para saber se deve disparar o jumpscare
        roteirizado deste frame (evento 'jumpscare_event')."""
        flag = getattr(self, "_jumpscare_flag", False)
        if flag:
            self._jumpscare_flag = False
            return True
        return False
