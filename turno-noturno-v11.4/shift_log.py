"""Histórico limitado do turno. O relatório usa acontecimentos reais da partida."""
from collections import deque


class ShiftLog:
    def __init__(self):
        self.events = deque(maxlen=40)

    def record(self, seconds, text, patient_id=None):
        self.events.append({"seconds": seconds, "text": text, "patient_id": patient_id})

    def loss_report(self, patients, elapsed, medication):
        lost = [p for p in patients if p.is_lost()]
        lost_ids = {p.id for p in lost}
        relevant = [e.copy() for e in self.events if e["patient_id"] is None or e["patient_id"] in lost_ids]
        details = []
        for patient in lost:
            if patient.protocol_cooldown > 0:
                protocol = f"protocolo em recarga ({patient.protocol_cooldown:.0f}s restantes)"
            elif patient.protocol_failed:
                protocol = "protocolo interrompido antes da recuperação"
            else:
                protocol = "protocolo disponível"
            details.append(f"{patient.name}: {protocol}.")
        return {
            "seconds": elapsed,
            "patients": ", ".join(p.name for p in lost),
            "causes": [f"{p.name}: {p.death_reason or 'a estabilidade chegou a zero.'}" for p in lost],
            "details": details,
            "events": relevant[-3:],
            "delivered": medication.delivered,
            "expired": medication.expired,
        }
