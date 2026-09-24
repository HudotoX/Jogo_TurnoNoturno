"""Pedidos e bandeja: estado puro, sem dependência de áudio ou interface.

Os nomes são fictícios e não representam prescrições reais.
"""

from dataclasses import dataclass
import random
import settings as cfg


@dataclass(frozen=True)
class Medicine:
    code: str
    name: str
    color: tuple
    symbol: str
    shortcut: str


MEDICINES = (
    Medicine("A", "Lume", (215, 162, 65), "circle", "Q"),
    Medicine("B", "Aster", (105, 167, 206), "triangle", "W"),
    Medicine("C", "Nimbo", (143, 180, 120), "square", "E"),
    Medicine("D", "Vesper", (182, 126, 181), "diamond", "Z"),
    Medicine("E", "Orbe", (204, 120, 97), "cross", "X"),
    Medicine("F", "Nexo", (115, 187, 183), "bars", "C"),
)
MEDICINE_BY_CODE = {medicine.code: medicine for medicine in MEDICINES}


@dataclass
class Request:
    patient_id: int
    required: tuple
    duration: float
    remaining: float
    last_known_room: str
    tutorial: bool = False
    accepted: bool = False


class MedicationManager:
    def __init__(self, rng=None):
        self.rng = rng if rng is not None else random.Random()
        self.active = None
        self.tray = []
        self.next_in = cfg.REQUEST_FIRST_AT
        self.tutorial_started = False
        self.delivered = 0
        self.expired = 0

    def update(self, dt, elapsed, patients):
        if self.active is not None:
            request = self.active
            request.remaining = max(0.0, request.remaining - dt)
            if request.remaining > 0:
                return None
            patient = self.patient(patients)
            penalty = 0 if request.tutorial else cfg.REQUEST_EXPIRY_PENALTY
            if patient is not None:
                patient.apply_loss(penalty, "O prazo do pedido acabou e a penalidade zerou a estabilidade.")
            self.expired += 1
            self._finish(patient)
            text = ("Primeiro pedido encerrado sem penalidade. Tente o próximo."
                    if request.tutorial else f"Pedido expirou: -{penalty} de estabilidade.")
            return {"kind": "expired", "patient_id": request.patient_id, "text": text}

        self.next_in = max(0.0, self.next_in - dt)
        if self.next_in > 0:
            return None
        candidates = [p for p in patients if not p.is_lost() and not p.is_hidden and not p.in_protocol]
        if not candidates:
            return None
        tutorial = not self.tutorial_started
        if tutorial:
            patient = next((p for p in candidates if p.id == 2), None)
            if patient is None:
                return None  # o atendimento guiado aguarda o fim do protocolo do Paciente 02
            count = 1
        else:
            patient = self.rng.choice(candidates)
            count = self.rng.choices((1, 2, 3), weights=cfg.REQUEST_SIZE_WEIGHTS, k=1)[0]
        duration = cfg.REQUEST_TUTORIAL_SECONDS if tutorial else cfg.REQUEST_SECONDS[count]
        if elapsed + duration + 5 > cfg.NIGHT_DURATION_SECONDS:
            # Não cria uma tarefa que o amanhecer impediria de concluir.
            self.next_in = cfg.NIGHT_DURATION_SECONDS
            return None
        codes = ("A",) if tutorial else tuple(self.rng.sample(tuple(MEDICINE_BY_CODE), count))
        self.active = Request(patient.id, codes, duration, duration, patient.room, tutorial)
        self.tutorial_started = True
        patient.movement_locked = tutorial
        # O chamado informa o canal naquele instante, sem rastrear movimentos futuros.
        patient.last_known_room = patient.room
        return {"kind": "started", "patient_id": patient.id,
                "text": f"Novo pedido recebido pela {patient.room}."}

    def patient(self, patients):
        if self.active is None:
            return None
        return next((p for p in patients if p.id == self.active.patient_id), None)

    def accept(self):
        if self.active is None or self.active.accepted:
            return False
        self.active.accepted = True
        return True

    def pick(self, code):
        if self.active is None or not self.active.accepted:
            return False, "Ouça o pedido do paciente antes de retirar itens."
        if code not in MEDICINE_BY_CODE:
            return False, "Item desconhecido."
        if code in self.tray:
            return False, "Este item já está na bandeja."
        if len(self.tray) >= cfg.TRAY_CAPACITY:
            return False, "Bandeja cheia. Remova um item para trocar."
        self.tray.append(code)
        return True, f"{MEDICINE_BY_CODE[code].name} adicionado à bandeja."

    def remove(self, index):
        if not 0 <= index < len(self.tray):
            return False
        self.tray.pop(index)
        return True

    def ready(self):
        return (self.active is not None and self.active.accepted
                and len(self.tray) == len(self.active.required)
                and set(self.tray) == set(self.active.required))

    def deliver(self, patient):
        if self.active is None or patient.id != self.active.patient_id or patient.is_lost():
            return False, "Localize o paciente que fez o pedido."
        if not self.ready():
            return False, "Confira a lista: entregue todos os itens pedidos, sem extras."
        gain = cfg.REQUEST_STABILITY_GAIN[len(self.active.required)]
        before = patient.stability
        patient.stability = min(cfg.STABILITY_MAX, before + gain)
        patient._recompute_state()
        patient.refresh_reading()
        self.delivered += 1
        self._finish(patient)
        return True, f"Entrega concluída: +{patient.stability - before:.0f} de estabilidade."

    def _finish(self, patient):
        if patient is not None:
            patient.movement_locked = False
        self.active = None
        self.tray.clear()
        self.next_in = self.rng.uniform(cfg.REQUEST_INTERVAL_MIN, cfg.REQUEST_INTERVAL_MAX)
