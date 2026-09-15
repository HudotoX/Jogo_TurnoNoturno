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
                 decay_mult=1.0, protocol_drain_mult=1.0, call_window_mult=1.0):
        self.id = patient_id
        self.name = name
        self.theme = theme  # texto curto do tema (ex: "Ansiedade")
        self.room = start_room
        self.profile = profile  # "anxiety" (Paciente 01) ou "perception" (Paciente 02)

        # Multiplicadores de dificuldade da noite atual (ver
        # settings.NIGHT_DIFFICULTY) — repassados pelo game.py na criação.
        self.decay_mult = decay_mult
        self.protocol_drain_mult = protocol_drain_mult
        self.call_window = cfg.CALL_RESPONSE_WINDOW * call_window_mult

        self.stability = cfg.STABILITY_MAX
        self.state = cfg.STATE_NORMAL

        # ---------- Última leitura conhecida (ver settings/ui: estabilidade
        # só é mostrada de verdade na câmera onde o paciente está) ----------
        self.last_known_stability = self.stability
        self.last_known_state = self.state
        self.seconds_since_seen = 0.0

        self.in_protocol = False
        self.protocol_progress = 0.0
        self.protocol_cooldown = 0.0  # tempo restante até poder acionar o protocolo de novo

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

        # ---------- Chamados (ver settings.CALL_*) ----------
        self.is_calling = False
        self._call_timer = 0.0
        self._call_cooldown = 8.0  # pequena folga antes do 1º chamado possível na noite

    # ------------------------------------------------------------------
    def update(self, dt, being_observed, rooms):
        """Retorna uma lista de eventos ocorridos neste frame (strings),
        atualmente só pode conter 'call_expired' — usado pelo game.py
        para tocar som/logar sem acoplar patient.py em audio/UI."""
        events = []

        # cooldown do protocolo conta mesmo fora de protocolo
        self.protocol_cooldown = max(0.0, self.protocol_cooldown - dt)
        self._call_cooldown = max(0.0, self._call_cooldown - dt)

        if self.in_protocol:
            # decaimento normal fica pausado; ver update_protocol() para a
            # queda de estabilidade específica do protocolo. Chamados
            # também não avançam — o jogador já está ocupado.
            return events

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

        decay = cfg.DECAY_OBSERVED if being_observed else cfg.DECAY_UNOBSERVED
        if self.profile == "perception" and not being_observed:
            decay *= 1.15
        decay *= self._crisis_multiplier
        decay *= self.decay_mult

        self.stability = max(0.0, self.stability - decay * dt)
        self._recompute_state()

        # a "leitura" só atualiza de verdade enquanto o jogador está com a
        # câmera certa aberta — fora disso, a HUD mostra este snapshot
        # congelado (ver ui.py: draw_stability_bar_locked) em vez do valor
        # real, que segue mudando por baixo dos panos.
        if being_observed:
            self.last_known_stability = self.stability
            self.last_known_state = self.state
            self.seconds_since_seen = 0.0
        else:
            self.seconds_since_seen += dt

        self._room_change_cooldown = max(0.0, self._room_change_cooldown - dt)
        if self.state in (cfg.STATE_MOVENDO, cfg.STATE_ANORMAL, cfg.STATE_PERIGO):
            if self._room_change_cooldown <= 0 and random.random() < cfg.ROOM_CHANGE_CHANCE * dt * 10:
                self.move_to_random_room(rooms)
                self._room_change_cooldown = 3.0

        # ---------- Chamados ----------
        if self.is_calling:
            self._call_timer -= dt
            if self._call_timer <= 0:
                self.is_calling = False
                self.stability = max(0.0, self.stability - cfg.CALL_STABILITY_PENALTY)
                self._recompute_state()
                self._call_cooldown = cfg.CALL_COOLDOWN_SECONDS
                events.append("call_expired")
        elif (self._call_cooldown <= 0 and self.state in
              (cfg.STATE_MOVENDO, cfg.STATE_ANORMAL, cfg.STATE_PERIGO)):
            if random.random() < cfg.CALL_AUTOCALL_CHANCE * dt:
                self.start_call()
                events.append("call_started")

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
        choices = [r for r in rooms if r != self.room]
        if choices:
            self.room = random.choice(choices)

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
    def start_call(self, scripted=False):
        """Liga o chamado deste paciente. scripted=True é usado por
        eventos roteirizados (nights.py) e ignora o cooldown normal, pra
        garantir que um beat de roteiro sempre dispare."""
        if self.in_protocol or (self.is_calling and not scripted):
            return
        if not scripted and self._call_cooldown > 0:
            return
        self.is_calling = True
        self._call_timer = self.call_window

    def answer_call(self):
        """Chamado pelo game.py quando o jogador responde a tempo (câmera
        certa + tecla de resposta). Retorna True se havia um chamado
        ativo para responder."""
        if not self.is_calling:
            return False
        self.is_calling = False
        self._call_timer = 0.0
        self.stability = min(cfg.STABILITY_MAX, self.stability + cfg.CALL_STABILITY_GAIN)
        self._recompute_state()
        self._call_cooldown = cfg.CALL_COOLDOWN_SECONDS
        return True

    # ------------------------------------------------------------------
    def start_protocol(self):
        self.in_protocol = True
        self.protocol_progress = 0.0

    def update_protocol(self, dt, holding):
        """Chamado a cada frame enquanto o protocolo está ativo.
        Retorna 'success', 'failed' ou 'ongoing'.

        A estabilidade continua caindo mesmo durante o protocolo — é
        isso que cria a necessidade de precisão: iniciar cedo demais é
        seguro, mas deixar chegar quase no fundo antes de agir é
        arriscado de verdade.
        """
        if not self.in_protocol:
            return "ongoing"

        self.stability = max(0.0, self.stability - cfg.PROTOCOL_DRAIN_RATE * self.protocol_drain_mult * dt)
        self._recompute_state()
        # o overlay do protocolo mostra a estabilidade real em tempo real,
        # então a "última leitura" da HUD acompanha isso — não faria
        # sentido voltar pra câmera e ver um número desatualizado do que o
        # jogador acabou de assistir acontecer na tela.
        self.last_known_stability = self.stability
        self.last_known_state = self.state
        self.seconds_since_seen = 0.0

        if self.stability <= 0:
            self.in_protocol = False
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
        self.in_protocol = False
        self.protocol_progress = 0.0
        self.protocol_cooldown = cfg.PROTOCOL_COOLDOWN_SECONDS
        self.is_glitched = False
        self._glitch_timer = 0.0
        self.is_hidden = False
        self.is_calling = False
        self._call_timer = 0.0

    # ------------------------------------------------------------------
    def can_start_protocol(self):
        return not self.in_protocol and self.protocol_cooldown <= 0 and self.stability < cfg.STABILITY_MAX

    def needs_protocol(self):
        return self.stability <= cfg.PROTOCOL_TRIGGER_THRESHOLD and self.can_start_protocol()

    def on_protocol_cooldown(self):
        return self.protocol_cooldown > 0 and not self.in_protocol

    def is_critical(self):
        return self.state == cfg.STATE_PERIGO

    def is_lost(self):
        return self.stability <= 0

    def call_time_left(self):
        """Fração (0-1) do tempo restante para responder o chamado atual —
        usado só pela UI para desenhar a barrinha de urgência."""
        if not self.is_calling or self.call_window <= 0:
            return 0.0
        return max(0.0, self._call_timer / self.call_window)

    # ------------------------------------------------------------------
    def status_line(self):
        return f"{self.name} — {self.theme} — {self.state}"
