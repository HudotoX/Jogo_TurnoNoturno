"""Abertura, legendas do rádio, diário e desfechos dentro do VIGIA."""
import pygame
import settings as cfg
from story import CLUES, INTRO_PAGES


class StoryUI:
    @staticmethod
    def story_window_rect():
        rect = pygame.Rect(0, 0, 1220, 840)
        rect.center = (cfg.WIDTH // 2, (cfg.HEIGHT - cfg.TASKBAR_HEIGHT) // 2)
        return rect

    @classmethod
    def story_close_rect(cls):
        rect = cls.story_window_rect()
        return pygame.Rect(rect.right - 25, rect.top + 7, 18, 18)

    @classmethod
    def intro_button_rects(cls):
        rect = cls.story_window_rect()
        return (pygame.Rect(rect.left + 34, rect.bottom - 74, 180, 44),
                pygame.Rect(rect.right - 354, rect.bottom - 74, 320, 44))

    @classmethod
    def ending_choice_rects(cls):
        rect = cls.story_window_rect()
        return [pygame.Rect(rect.left + 40, rect.bottom - 190 + index * 68, rect.width - 80, 54)
                for index in range(2)]

    @classmethod
    def ending_return_rect(cls):
        rect = cls.story_window_rect()
        return pygame.Rect(rect.centerx - 170, rect.bottom - 82, 340, 48)

    @classmethod
    def ending_record_rects(cls):
        win = cls.story_window_rect()
        return [pygame.Rect(win.left + 36, win.top + 354 + i * 41, win.width - 72, 36)
                for i in range(len(CLUES))]

    @staticmethod
    def story_strip_rect(feed):
        return pygame.Rect(feed.left + 16, feed.bottom - 152, feed.width - 32, 132)

    @classmethod
    def record_button_rect(cls, feed):
        box = cls.story_strip_rect(feed)
        return pygame.Rect(box.right - 282, box.top + 74, 264, 42)

    def _story_button(self, surface, rect, text, selected=False):
        self.draw_bevel_rect(surface, rect, raised=not selected)
        label = self.font_care_bold.render(text, True, cfg.WIN95_TEXT)
        surface.blit(label, label.get_rect(center=rect.center))
        if selected:
            self._draw_dotted_rect(surface, rect.inflate(-10, -10), cfg.WIN95_TEXT)

    def draw_story_intro(self, surface, page_index):
        surface.fill(cfg.WIN95_DESKTOP_TEAL)
        self.draw_taskbar(surface)
        win = self.story_window_rect()
        _, body, _ = self.draw_window_chrome(surface, win, "PLANTAO.TXT — Noite 1")
        page = INTRO_PAGES[page_index]
        self._care_text(surface, page["title"], pygame.Rect(body.left + 28, body.top + 22, 920, 56),
                        font=self.font_large, line_height=44)
        count = f"{page_index + 1} / {len(INTRO_PAGES)}"
        self._care_text(surface, count, pygame.Rect(body.right - 112, body.top + 32, 100, 34))
        box = pygame.Rect(body.left + 28, body.top + 90, body.width - 56, body.height - 220)
        self.draw_bevel_rect(surface, box, raised=False, face=(225, 225, 216))
        visible = self._lore_text[:int(self._lore_reveal_chars)]
        self._care_text(surface, visible, box.inflate(-42, -34), font=self.font_story, line_height=35)
        back, advance = self.intro_button_rects()
        if page_index > 0:
            self._story_button(surface, back, "Voltar")
        label = "Iniciar turno" if page_index == len(INTRO_PAGES) - 1 else "Continuar"
        if not self.lore_fully_revealed():
            label = "Mostrar texto completo"
        self._story_button(surface, advance, label, selected=True)
        hint = "Clique nos botões ou use ENTER / seta esquerda · X ou ESC volta ao menu"
        self._care_text(surface, hint, pygame.Rect(body.left + 28, box.bottom + 22, body.width - 56, 32),
                        color=cfg.WIN95_TEXT_DIM)

    def draw_story_strip(self, surface, game, feed):
        box = self.story_strip_rect(feed)
        self.draw_bevel_rect(surface, box, raised=False, face=(215, 217, 206))
        story = game.story
        message = story.current
        if message is None:
            speaker = "MARINA DUARTE · DIÁRIO DO PLANTÃO"
            text = "Cuide de Daniel e Elias até as seis. Os registros que você guardar acompanharão a decisão no fim do turno."
        else:
            speaker, text = message.speaker, message.text
        text_width = box.width - 330
        self._care_text(surface, speaker, pygame.Rect(box.left + 16, box.top + 10, text_width, 30),
                        font=self.font_care_bold, color=(20, 47, 64))
        self._care_text(surface, text, pygame.Rect(box.left + 16, box.top + 43, text_width, 80),
                        font=self.font_story_small, line_height=26)
        pending = story.pending_clue
        if pending is not None:
            title = CLUES[pending]["title"]
            self._care_text(surface, f"PENDENTE · {title}", pygame.Rect(box.right - 280, box.top + 12, 260, 56),
                            font=self.font_care_bold, color=(107, 59, 17))
            self._story_button(surface, self.record_button_rect(feed), "[F] Guardar registro")
        else:
            self._care_text(surface, f"REGISTROS GUARDADOS\n{len(story.recorded)} / {len(CLUES)}",
                            pygame.Rect(box.right - 280, box.top + 26, 260, 80), color=cfg.WIN95_TEXT_DIM)

    def draw_story_journal(self, surface, game, box):
        self.draw_bevel_rect(surface, box, raised=False, face=(222, 224, 212))
        pending = game.story.pending_clue
        text = f"DIÁRIO · {len(game.story.recorded)}/{len(CLUES)} registros\n"
        if pending is not None:
            text += "Há uma descoberta para guardar. Use F ou o botão na legenda."
        elif game.night_elapsed >= 165:
            text += "Prévia do VIGIA:\nSEM OCORRÊNCIAS"
        else:
            text += "Escute os relatos e confira os arquivos do hospital."
        self._care_text(surface, text, box.inflate(-20, -16))

    def draw_story_ending(self, surface, story, delivered):
        surface.fill(cfg.WIN95_DESKTOP_TEAL)
        self.draw_taskbar(surface)
        win = self.story_window_rect()
        _, body, _ = self.draw_window_chrome(surface, win, "RELATORIO.TXT — Encerramento do plantão",
                                            closable=story.choice is not None)
        if story.choice is None:
            self._care_text(surface, "06h00 · O que fica registrado?",
                            pygame.Rect(body.left + 30, body.top + 20, body.width - 60, 58), font=self.font_large)
            self._care_text(surface, f"Daniel e Elias chegaram ao amanhecer. Entregas concluídas: {delivered}.",
                            pygame.Rect(body.left + 30, body.top + 82, body.width - 60, 38), font=self.font_story)
            report = pygame.Rect(body.left + 30, body.top + 138, body.width - 60, 110)
            self.draw_bevel_rect(surface, report, raised=False, face=(225, 225, 216))
            self._care_text(surface, "RELATÓRIO AUTOMÁTICO DO VIGIA\n"
                            "“SEM OCORRÊNCIAS. Relatos classificados como falhas de percepção.”",
                            report.inflate(-28, -24), font=self.font_story, line_height=35)
            y = report.bottom + 28
            self._care_text(surface, f"Seu diário: {len(story.recorded)} de {len(CLUES)} registros guardados.",
                            pygame.Rect(body.left + 30, y, body.width - 60, 34), font=self.font_story)
            y += 45
            for (key, clue), row in zip(CLUES.items(), self.ending_record_rects()):
                if key in story.recorded:
                    line = f"[RELER] {clue['title']} · {clue['source']}"
                    self.draw_bevel_rect(surface, row, raised=story.review_key != key,
                                         face=cfg.WIN95_FACE_LIGHT)
                elif key in story.discovered:
                    line = f"[NÃO GUARDADO] {clue['title']}"
                else:
                    line = "[NÃO ENCONTRADO] Há uma lacuna nas suas anotações."
                self._care_text(surface, line, pygame.Rect(row.left + 10, row.top + 5, row.width - 20, 30))
                y += 41
            detail = (CLUES[story.review_key]["text"] if story.review_key in story.recorded else
                      "Clique num registro para reler. Você pode anexar seu diário e contestar o relatório, "
                      "ou assinar a versão automática.")
            self._care_text(surface, detail,
                            pygame.Rect(body.left + 30, y + 12, body.width - 60, 94), font=self.font_story_small)
            labels = ("Anexar meu diário e contestar o relatório", "Assinar o relatório automático")
            for index, (rect, label) in enumerate(zip(self.ending_choice_rects(), labels)):
                self._story_button(surface, rect, label, selected=index == story.ending_selected)
            self._care_text(surface, "Setas escolhem · ENTER confirma · mouse também funciona",
                            pygame.Rect(body.left + 30, body.bottom - 36, body.width - 60, 28), color=cfg.WIN95_TEXT_DIM)
        else:
            title, paragraphs = story.ending()
            self._care_text(surface, title, pygame.Rect(body.left + 30, body.top + 28, body.width - 60, 60),
                            font=self.font_large)
            box = pygame.Rect(body.left + 30, body.top + 114, body.width - 60, body.height - 260)
            self.draw_bevel_rect(surface, box, raised=False, face=(225, 225, 216))
            self._care_text(surface, "\n\n".join(paragraphs), box.inflate(-42, -34),
                            font=self.font_story, line_height=37)
            self._care_text(surface, "FIM DA NOITE 1 · Sua escolha encerra esta história.",
                            pygame.Rect(body.left + 30, box.bottom + 24, body.width - 60, 38), color=cfg.WIN95_TEXT_DIM)
            self._story_button(surface, self.ending_return_rect(), "Voltar ao menu [ENTER]", selected=True)
