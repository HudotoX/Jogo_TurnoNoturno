"""Interface dos pedidos, farmácia e bandeja, no mesmo estilo do VIGIA."""
import math
import pygame
import settings as cfg
from medication import MEDICINES, MEDICINE_BY_CODE


class CareUI:
    @staticmethod
    def request_panel_rect(feed):
        return pygame.Rect(feed.right + 12, feed.top, cfg.WIDTH - feed.right - 32, feed.height)

    @staticmethod
    def request_action_rect(panel):
        return pygame.Rect(panel.left + 16, panel.top + 350, panel.width - 32, 44)

    @staticmethod
    def tray_rects(panel):
        return [pygame.Rect(panel.left + 16, panel.top + 444 + i * 46, panel.width - 32, 40)
                for i in range(cfg.TRAY_CAPACITY)]

    @staticmethod
    def pharmacy_item_rects(feed):
        gap, margin = 24, 60
        width = (feed.width - 2 * margin - 2 * gap) // 3
        height = 210
        top = feed.top + 176
        return [pygame.Rect(feed.left + margin + (i % 3) * (width + gap),
                            top + (i // 3) * (height + gap), width, height)
                for i in range(len(MEDICINES))]

    def _care_text(self, surface, text, rect, color=None, font=None, line_height=25):
        font = font or self.font_care
        color = cfg.WIN95_TEXT if color is None else color
        previous = surface.get_clip()
        surface.set_clip(rect.clip(previous))
        try:
            for index, line in enumerate(self._wrap_text(text, font, rect.width)):
                surface.blit(font.render(line, True, color), (rect.left, rect.top + index * line_height))
        finally:
            surface.set_clip(previous)

    @staticmethod
    def _medicine_symbol(surface, medicine, center, size=14):
        x, y = center
        color = (22, 25, 28)
        if medicine.symbol == "circle":
            pygame.draw.circle(surface, color, (x, y), size, 3)
        elif medicine.symbol == "triangle":
            pygame.draw.polygon(surface, color, [(x, y-size), (x+size, y+size), (x-size, y+size)], 3)
        elif medicine.symbol == "square":
            pygame.draw.rect(surface, color, (x-size, y-size, size*2, size*2), 3)
        elif medicine.symbol == "diamond":
            pygame.draw.polygon(surface, color, [(x, y-size), (x+size, y), (x, y+size), (x-size, y)], 3)
        elif medicine.symbol == "cross":
            pygame.draw.line(surface, color, (x-size, y), (x+size, y), 5)
            pygame.draw.line(surface, color, (x, y-size), (x, y+size), 5)
        else:
            for offset in (-size//2, size//2):
                pygame.draw.line(surface, color, (x+offset, y-size), (x+offset, y+size), 5)

    def draw_pharmacy(self, surface, game, feed):
        if game.camera_system.is_blackout:
            return
        heading = pygame.Rect(feed.left + 60, feed.top + 52, feed.width - 120, 98)
        self.draw_bevel_rect(surface, heading, face=cfg.WIN95_FACE)
        self._care_text(surface, "ALA FARMACÊUTICA / DISPENSAÇÃO", heading.inflate(-28, -16),
                        font=self.font_large, line_height=42)
        self._care_text(surface, "Retire com o mouse ou Q / W / E / Z / X / C. Confira o pedido à direita.",
                        pygame.Rect(heading.left + 16, heading.top + 60, heading.width - 32, 30))
        request = game.medication.active
        enabled = request is not None and request.accepted
        for medicine, rect in zip(MEDICINES, self.pharmacy_item_rects(feed)):
            picked = medicine.code in game.medication.tray
            face = (180, 194, 183) if picked else cfg.WIN95_FACE
            self.draw_bevel_rect(surface, rect, raised=not picked, face=face)
            if enabled and request.tutorial and medicine.code in request.required:
                pygame.draw.rect(surface, (20, 92, 65), rect.inflate(-8, -8), 3)
            # Frasco e símbolo são desenhos da interface, sem dependências de imagem.
            bottle = pygame.Rect(rect.left + 24, rect.top + 48, 80, 98)
            pygame.draw.rect(surface, (232, 233, 220), bottle, border_radius=8)
            pygame.draw.rect(surface, (45, 48, 50), bottle, 2, border_radius=8)
            pygame.draw.rect(surface, (69, 72, 73), (bottle.left + 8, bottle.top - 16, 64, 20))
            label = pygame.Rect(bottle.left + 2, bottle.top + 23, bottle.width - 4, 53)
            pygame.draw.rect(surface, medicine.color, label)
            self._medicine_symbol(surface, medicine, label.center)
            self._care_text(surface, f"{medicine.code} / {medicine.name}",
                            pygame.Rect(rect.left + 124, rect.top + 54, rect.width - 140, 64),
                            font=self.font_care_bold, line_height=27)
            status = "NA BANDEJA" if picked else f"[{medicine.shortcut}] Retirar"
            if not enabled:
                status = "Aguardando pedido"
            self._care_text(surface, status,
                            pygame.Rect(rect.left + 24, rect.bottom - 44, rect.width - 48, 30),
                            color=(25, 86, 49) if picked else cfg.WIN95_TEXT)
        # A faixa inferior é ocupada pelo rádio/diário; os controles da bandeja ficam no painel.

    def draw_request_panel(self, surface, game, panel):
        self.draw_bevel_rect(surface, panel)
        title = pygame.Rect(panel.left + 3, panel.top + 3, panel.width - 6, 30)
        pygame.draw.rect(surface, cfg.WIN95_TITLE_ACTIVE, title)
        self._care_text(surface, "ATENDIMENTO / PEDIDOS", title.inflate(-16, -4),
                        color=cfg.WIN95_TITLE_TEXT, font=self.font_care_bold)
        manager, request = game.medication, game.medication.active
        x, width = panel.left + 16, panel.width - 32
        patient = manager.patient(game.patients)
        if request is None:
            headline = "Nenhum pedido pendente"
            if not manager.tutorial_started:
                hint = ("Alterne CAM 01 / CAM 03. Clique em Estabilizar e segure o botão do protocolo. "
                        "O chamado chega em instantes.")
            else:
                hint = "Continue alternando as câmeras e estabilizando os pacientes. Aguarde o próximo chamado."
            timer_text = f"Entregas concluídas: {manager.delivered}"
        else:
            step = "1/3 Ouvir" if not request.accepted else ("3/3 Entregar" if manager.ready() else "2/3 Buscar")
            headline = f"{patient.name} — {step}"
            timer_text = f"Prazo: {math.ceil(request.remaining)}s"
            if request.tutorial:
                timer_text += " · primeiro atendimento"
            room = request.last_known_room
            if not request.accepted:
                hint = f"Último contato: {room}. Encontre o paciente e clique em Ouvir pedido (R)."
            elif manager.ready():
                hint = f"Volte ao paciente e clique em Entregar (R). Último contato: {room}."
            else:
                hint = "Abra a Farmácia (F5), clique nos itens da lista e volte ao paciente para entregar."
        self._care_text(surface, headline, pygame.Rect(x, panel.top + 46, width, 30), font=self.font_care_bold)
        color = (140, 34, 34) if request and request.remaining < 10 else cfg.WIN95_TEXT_DIM
        self._care_text(surface, timer_text, pygame.Rect(x, panel.top + 79, width, 30), color=color)
        self._care_text(surface, hint, pygame.Rect(x, panel.top + 116, width, 100))

        if request and request.accepted:
            for index, code in enumerate(request.required):
                medicine = MEDICINE_BY_CODE[code]
                row = pygame.Rect(x, panel.top + 220 + index * 38, width, 32)
                pygame.draw.rect(surface, cfg.WIN95_FACE_LIGHT, row)
                pygame.draw.rect(surface, medicine.color, (row.left + 4, row.top + 3, 28, 26))
                self._medicine_symbol(surface, medicine, (row.left + 18, row.centery), 8)
                text = f"{code} / {medicine.name}" + ("  [OK]" if code in manager.tray else "")
                self._care_text(surface, text, pygame.Rect(row.left + 42, row.top + 4, row.width - 48, 28))
        else:
            text = "A lista ficará visível após ouvir o paciente." if request else "Protocolos: recuperação maior.\nEntregas: reforço entre protocolos."
            self._care_text(surface, text, pygame.Rect(x, panel.top + 232, width, 86), color=cfg.WIN95_TEXT_DIM)
        action = self.request_action_rect(panel)
        available = game._visible(patient) and request is not None
        self.draw_bevel_rect(surface, action, raised=True)
        label = "[R] Ouvir pedido" if request and not request.accepted else "[R] Entregar bandeja"
        if request is None:
            label = "Aguardando chamado"
        self._care_text(surface, label, action.inflate(-16, -12), font=self.font_care_bold,
                        color=cfg.WIN95_TEXT if available else cfg.WIN95_TEXT_DIM)

        self._care_text(surface, f"BANDEJA {len(manager.tray)}/3 · clique para remover",
                        pygame.Rect(x, panel.top + 413, width, 28))
        for index, rect in enumerate(self.tray_rects(panel)):
            self.draw_bevel_rect(surface, rect, raised=False, face=cfg.WIN95_FACE_LIGHT)
            if index < len(manager.tray):
                medicine = MEDICINE_BY_CODE[manager.tray[index]]
                pygame.draw.rect(surface, medicine.color, (rect.left + 7, rect.top + 8, 24, 24))
                self._medicine_symbol(surface, medicine, (rect.left + 19, rect.top + 20), 8)
                text = f"{medicine.code} / {medicine.name}"
                self._care_text(surface, text, pygame.Rect(rect.left + 42, rect.top + 9, rect.width - 80, 30))
                self._care_text(surface, "×", pygame.Rect(rect.right - 28, rect.top + 8, 24, 26))
            else:
                self._care_text(surface, "— vazio —", rect.inflate(-18, -14), color=cfg.WIN95_TEXT_DIM)
        if game.feedback_timer > 0:
            self._care_text(surface, game.feedback, pygame.Rect(x, panel.top + 594, width, 76), color=(30, 61, 99))
        elif request and request.tutorial:
            self._care_text(surface, "Dica: o primeiro pedido não aplica penalidade se o prazo acabar.",
                            pygame.Rect(x, panel.top + 594, width, 76), color=cfg.WIN95_TEXT_DIM)
        else:
            self._care_text(surface, "Clique num item da bandeja para remover.\nBACKSPACE remove o último.",
                            pygame.Rect(x, panel.top + 594, width, 76), color=cfg.WIN95_TEXT_DIM)
        speech = pygame.Rect(x, panel.top + 684, width, panel.height - 700)
        self.draw_story_journal(surface, game, speech)

    def draw_protocol_request_hint(self, surface, request):
        if request is None:
            return
        protocol = self.protocol_window_rect()
        box = pygame.Rect(protocol.centerx - 320, protocol.bottom + 16, 640, 90)
        self.draw_bevel_rect(surface, box)
        self._care_text(surface, f"Pedido do Paciente {request.patient_id:02d}: {math.ceil(request.remaining)}s restantes.\n"
                        "O prazo continua correndo durante o protocolo.", box.inflate(-28, -20))
