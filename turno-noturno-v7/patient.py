"""
patient.py
Modelo de paciente: posição/sala, estado, estabilidade e comportamento.
Sem IA complexa: apenas uma máquina de estados simples derivada da
estabilidade + timers/probabilidades para movimentação e eventos.
"""

import random
import settings as cfg


class Patient:
    def __init__(self, patient_id, name, theme, start_room, profile="anxiety",
                 decay_mult=1.0, protocol_drain_mult=1.0):
        self.id = patient_id
        self.name = name
        self.theme = theme  # texto curto do tema (ex: "Ansiedade")
        self.room = start_room
        self.profile = profile  # "anxiety" (Paciente 01) ou "perception" (Paciente 02)

        # Multiplicadores de dificuldade da noite atual (ver
        # settings.NIGHT_DIFFICULTY) — repassados pelo game.py na criação.
        self.decay_mult = decay_mult
        self.protocol_drain_mult = protocol_drain_mult

        self.stability = cfg.STABILITY_MAX
        self.state = cfg.STATE_NORMAL

        # ---------- Última leitura conhecida (ver settings/ui: estabilidade
        # só é mostrada de verdade na câmera onde o paciente está) ----------
        self.last_known_stability = self.stability
        self.last_known_state = self.state
        self.last_known_room = self.room
        self.seconds_since_seen = 0.0

        self.in_protocol = False
        self.protocol_progress = 0.0
        self.protocol_cooldown = 0.0  # tempo restante até poder acionar o protocolo de novo
        self.protocol_failed = False

        # Flags de comportamento usadas por eventos especiais
        self.is_glitched = False       # aparência anômala (visual de anomalia OU alarme falso)
        self._glitch_timer = 0.0
        self.is_hidden = False         # temporariamente fora de todas as câmeras
        self._hidden_timer = 0.0

        # "Crise" real: só ligada por uma anomalia VERDADEIRA — acelera o
        # decaimento por um tempo. Alarmes falsos não ligam isso, então o
        # único jeito de diferenciar é observando a barra de estabilidade.
        self._crisis_multiplier = 1.0
        self._crisis_timer = 0.0

        self._room_change_cooldown = 0.0
        self.movement_locked = False  # primeiro atendimento guiado
        self.death_reason = ""

    # ------------------------------------------------------------------
    def update(self, dt, being_observed, rooms):
        """Atualiza estabilidade e posição; pedidos ficam no MedicationManager."""
        events = []

        # cooldown do protocolo conta mesmo fora de protocolo
        self.protocol_cooldown = max(0.0, self.protocol_cooldown - dt)

        if self.is_hidden:
            self._hidden_timer -= dt
            if self._hidden_timer <= 0:
                self.is_hidden = False

        if self._glitch_timer > 0:
            self._glitch_timer -= dt
            if self._glitch_timer <= 0:
                self.is_glitched = False

        if self._crisis_timer > 0:
            self._crisis_timer -= dt
            if self._crisis_timer <= 0:
                self._crisis_multiplier = 1.0

        if not self.in_protocol:
            decay = cfg.DECAY_OBSERVED if being_observed else cfg.DECAY_UNOBSERVED
            if self.profile == "perception" and not being_observed:
                decay *= 1.15
            decay *= self._crisis_multiplier
            decay *= self.decay_mult

            if self._crisis_multiplier > 1:
                reason = "A estabilidade chegou a zero durante uma crise, com queda acelerada."
            elif being_observed:
                reason = "A estabilidade chegou a zero; observar apenas desacelera a queda."
            else:
                reason = "A estabilidade chegou a zero enquanto o paciente estava sem observação."
            self.apply_loss(decay * dt, reason)

            # a "leitura" só atualiza enquanto a câmera certa está aberta.
            if being_observed:
                self.refresh_reading()
            else:
                self.seconds_since_seen += dt

            self._room_change_cooldown = max(0.0, self._room_change_cooldown - dt)
            if self.state in (cfg.STATE_MOVENDO, cfg.STATE_ANORMAL, cfg.STATE_PERIGO):
                if (self._room_change_cooldown <= 0
                        and random.random() < cfg.ROOM_CHANGE_CHANCE * dt):
                    if self.move_to_random_room(rooms):
                        events.append("moved")

        return events

    # ------------------------------------------------------------------
    def _recompute_state(self):
        s = self.stability
        if s >= cfg.STATE_THRESHOLDS[cfg.STATE_NORMAL]:
            self.state = cfg.STATE_NORMAL
        elif s >= cfg.STATE_THRESHOLDS[cfg.STATE_INQUIETO]:
            self.state = cfg.STATE_INQUIETO
        elif s >= cfg.STATE_THRESHOLDS[cfg.STATE_MOVENDO]:
            self.state = cfg.STATE_MOVENDO
        elif s >= cfg.STATE_THRESHOLDS[cfg.STATE_ANORMAL]:
            self.state = cfg.STATE_ANORMAL
        else:
            self.state = cfg.STATE_PERIGO

    # ------------------------------------------------------------------
    def move_to_random_room(self, rooms):
        if self.movement_locked or self.in_protocol or self.is_lost():
            return False
        choices = [r for r in rooms if r != self.room and r in cfg.PATIENT_ROOMS]
        if choices:
            self.room = random.choice(choices)
            self._room_change_cooldown = cfg.ROOM_CHANGE_COOLDOWN
            return True
        return False

    def apply_loss(self, amount, reason):
        before = self.stability
        self.stability = max(0.0, self.stability - max(0, amount))
        self._recompute_state()
        if before > 0 and self.stability <= 0:
            self.death_reason = reason

    def refresh_reading(self):
        self.last_known_stability = self.stability
        self.last_known_state = self.state
        self.last_known_room = self.room
        self.seconds_since_seen = 0.0

    # ------------------------------------------------------------------
    def trigger_glitch(self, duration=6.0):
        """Efeito visual de anomalia. Usado tanto por avistamentos reais
        quanto por alarmes falsos — propositalmente idêntico nos dois."""
        self.is_glitched = True
        self._glitch_timer = duration

    def trigger_crisis(self, multiplier=1.6, duration=10.0):
        """Só chamado em anomalias REAIS: acelera o decaimento por um
        tempo. Alarmes falsos nunca chamam isso."""
        self._crisis_multiplier = multiplier
        self._crisis_timer = duration

    # ------------------------------------------------------------------
    def start_protocol(self):
        if not self.can_start_protocol():
            return False
        self.in_protocol = True
        self.protocol_failed = False
        self.protocol_progress = 0.0
        # O pedido de medicamentos continua existindo, com o prazo correndo.
        return True

    def update_protocol(self, dt, holding):
        """Chamado a cada frame enquanto o protocolo está ativo.
        Retorna 'success', 'failed' ou 'ongoing'.

        A estabilidade continua caindo durante o protocolo. Enquanto o
        jogador opera esta tela, o restante do hospital também continua
        avançando normalmente em game.py.
        """
        if not self.in_protocol:
            return "ongoing"

        self.apply_loss(cfg.PROTOCOL_DRAIN_RATE * self.protocol_drain_mult * dt,
                        "A estabilidade acabou durante o protocolo, antes de completar "
                        f"os {cfg.PROTOCOL_HOLD_SECONDS:g} segundos.")
        # o overlay do protocolo mostra a estabilidade real em tempo real,
        # então a "última leitura" da HUD acompanha isso — não faria
        # sentido voltar pra câmera e ver um número desatualizado do que o
        # jogador acabou de assistir acontecer na tela.
        self.last_known_stability = self.stability
        self.last_known_state = self.state
        self.seconds_since_seen = 0.0

        if self.stability <= 0:
            self.in_protocol = False
            self.protocol_failed = True
            self.protocol_progress = 0.0
            return "failed"

        if holding:
            self.protocol_progress += dt
            if self.protocol_progress >= cfg.PROTOCOL_HOLD_SECONDS:
                self.complete_protocol()
                return "success"

        return "ongoing"

    def cancel_protocol(self):
        self.in_protocol = False
        self.protocol_progress = 0.0
        self.protocol_cooldown = cfg.PROTOCOL_CANCEL_COOLDOWN_SECONDS

    def complete_protocol(self):
        self.stability = min(cfg.STABILITY_MAX, self.stability + cfg.PROTOCOL_STABILITY_GAIN)
        self._recompute_state()
        self.last_known_stability = self.stability
        self.last_known_state = self.state
        self.seconds_since_seen = 0.0
        self.in_protocol = False
        self.protocol_progress = 0.0
        self.protocol_cooldown = cfg.PROTOCOL_COOLDOWN_SECONDS
        self.is_glitched = False
        self._glitch_timer = 0.0
        self.is_hidden = False

    # ------------------------------------------------------------------
    def can_start_protocol(self):
        return (not self.in_protocol and self.protocol_cooldown <= 0
                and self.stability > 0)

    def needs_protocol(self):
        return self.stability <= cfg.PROTOCOL_RECOMMEND_THRESHOLD and self.can_start_protocol()

    def on_protocol_cooldown(self):
        return self.protocol_cooldown > 0 and not self.in_protocol

    def is_critical(self):
        return self.state == cfg.STATE_PERIGO

    def is_lost(self):
        return self.stability <= 0

    def status_line(self):
        return f"{self.name} — {self.theme} — {self.state}"
