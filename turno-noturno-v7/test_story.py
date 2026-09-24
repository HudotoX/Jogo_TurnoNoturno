"""Integração da história com leitura, atendimento e encerramento do turno."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import settings as cfg
from game import Game, STATE_NIGHT_INTRO, STATE_PLAYING, STATE_NIGHT_END
from story import Story, INTRO_PAGES


class StoryRulesTests(unittest.TestCase):
    def test_pharmacy_requires_time_signal_and_available_interaction(self):
        story = Story()
        for elapsed, camera, blackout, available in (
            (89, "CAM 05", False, True), (100, "CAM 01", False, True),
            (100, "CAM 05", True, True), (100, "CAM 05", False, False),
        ):
            story.observe(elapsed, camera, blackout, available)
            self.assertFalse(story.discovered)
        story.observe(100, "CAM 05", False, True)
        story.observe(101, "CAM 05", False, True)
        self.assertEqual(story.discovered, ["ficha"])

    def test_important_radio_messages_wait_while_screen_is_covered(self):
        story = Story()
        story.on_delivery(2)
        story.update(0.1, 0)
        first = story.current
        remaining = story.message_left
        story.on_blackout()
        story.say("PACIENTE", "Obrigado de novo.", important=False)
        story.update(50, 0, can_read=False)
        self.assertIs(story.current, first)
        self.assertEqual(story.message_left, remaining)
        story.update(remaining, 0)
        self.assertIn("câmeras apagaram", story.current.text)
        self.assertFalse(story.queue)  # agradecimento rotineiro não acumulou

    def test_endings_respect_saved_evidence_and_final_choice(self):
        for count in range(4):
            for choice in ("preserve", "automatic"):
                with self.subTest(count=count, choice=choice):
                    story = Story()
                    story.on_delivery(1)
                    story.observe(100, "CAM 05", False, True)
                    story.on_blackout()
                    for _ in range(count):
                        story.record_next()
                    self.assertTrue(story.choose(choice))
                    self.assertFalse(story.choose("automatic" if choice == "preserve" else "preserve"))
                    title, paragraphs = story.ending()
                    if choice == "automatic":
                        self.assertEqual(title, "SEM OCORRÊNCIAS")
                    elif count >= 2:
                        self.assertEqual(title, "UMA NOITE REGISTRADA")
                        self.assertIn(f"{count} registros", " ".join(paragraphs))
                    else:
                        self.assertEqual(title, "O PRIMEIRO TESTEMUNHO")
                        self.assertIn("Sem registros" if count == 0 else "único registro", " ".join(paragraphs))


class StoryGameplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.game = Game(self.screen)
        self.game.start_night(1)
        self.game.event_manager.events = []
        self.random_patch = patch("patient.random.random", return_value=1)
        self.random_patch.start()

    def tearDown(self):
        self.random_patch.stop()
        self.game.audio.stop_ambient()

    def key(self, key):
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))

    def click(self, rect):
        self.game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))

    def test_intro_can_be_read_and_revisited_before_the_clock_starts(self):
        g = self.game
        self.key(pygame.K_RETURN)
        self.assertEqual(g.intro_page, 0)
        self.assertTrue(g.ui.lore_fully_revealed())
        self.click(g.ui.intro_button_rects()[1])
        self.assertEqual(g.intro_page, 1)
        self.key(pygame.K_LEFT)
        self.assertEqual(g.intro_page, 0)
        for page in range(len(INTRO_PAGES)):
            g.update(60)
            self.assertEqual(g.night_elapsed, 0)
            self.assertTrue(all(p.stability == 100 for p in g.patients))
            self.assertEqual(g.state, STATE_NIGHT_INTRO)
            self.assertEqual(g.intro_page, page)
            g.draw()
            self.key(pygame.K_RETURN)
        g.update(cfg.SCENE_TRANSITION_SECONDS)
        g.update(cfg.SCENE_TRANSITION_SECONDS)
        self.assertEqual(g.state, STATE_PLAYING)
        self.assertEqual(g.night_elapsed, 0)

    def test_recording_is_optional_unique_and_does_not_heal_or_reset_time(self):
        g = self.game
        g.state = STATE_PLAYING
        self.key(pygame.K_f)
        self.assertFalse(g.story.recorded)
        g.story.on_delivery(2)
        g.story.on_delivery(1)
        g.story.on_blackout()
        self.key(pygame.K_1)
        request_before = g.night_elapsed
        self.key(pygame.K_f)
        self.assertFalse(g.story.recorded)
        g.update(1)
        self.assertGreater(g.night_elapsed, request_before)
        self.key(pygame.K_ESCAPE)
        stability = [p.stability for p in g.patients]
        elapsed = g.night_elapsed
        self.key(pygame.K_f)
        self.assertEqual(g.story.recorded, ["relato"])
        g.trigger_jumpscare()
        self.click(g.ui.record_button_rect(g._playing_layout()[2]))
        self.assertEqual(g.story.recorded, ["relato"])
        g.update(cfg.JUMPSCARE_DURATION)
        self.click(g.ui.record_button_rect(g._playing_layout()[2]))
        self.key(pygame.K_f)
        self.assertEqual(g.story.recorded, ["relato", "falha"])
        self.assertEqual([p.stability for p in g.patients], stability)
        self.assertEqual(g.night_elapsed, elapsed)
        g.story.observe(100, "CAM 05", False, True)
        g.state = STATE_NIGHT_END
        g._try_record_clue()
        self.assertNotIn("ficha", g.story.recorded)
        g.start_night(1)
        self.assertFalse(g.story.recorded)
        self.assertFalse(g.story.discovered)
        self.assertIsNone(g.story.choice)

    def test_blackout_discovers_record_during_protocol_without_consuming_radio(self):
        g = self.game
        g.state = STATE_PLAYING
        self.key(pygame.K_1)
        g.event_manager.events = [{"time": 0.5, "type": "blackout", "payload": {}}]
        g.update(1)
        self.assertIn("falha", g.story.discovered)
        self.assertIsNone(g.story.current)
        self.assertFalse(g.story.recorded)
        self.assertEqual(g.night_elapsed, 1)
        self.click(g.ui.protocol_close_rect())
        self.assertIsNone(g.protocol_patient)
        self.assertEqual(g.patients[0].protocol_cooldown, cfg.PROTOCOL_CANCEL_COOLDOWN_SECONDS)
        g.update(0.1)
        self.assertIn("câmeras apagaram", g.story.current.text)

    def test_ending_record_click_only_reads_and_choices_work_by_mouse_or_keyboard(self):
        g = self.game
        g.state = STATE_NIGHT_END
        g.night_won = True
        g.story.on_delivery(2)
        g.story.record_next()
        self.click(g.ui.ending_record_rects()[0])
        self.assertEqual(g.story.review_key, "relato")
        self.assertIsNone(g.story.choice)
        self.click(g.ui.ending_record_rects()[1])
        self.assertEqual(g.story.review_key, "relato")
        self.click(pygame.Rect(0, 0, 2, 2))
        self.assertIsNone(g.story.choice)
        g.draw()
        self.key(pygame.K_DOWN)
        self.key(pygame.K_RETURN)
        self.assertEqual(g.story.choice, "automatic")
        g.draw()
        g.story = Story()
        self.click(g.ui.ending_choice_rects()[0])
        self.assertEqual(g.story.choice, "preserve")
        g.draw()
        self.click(g.ui.ending_return_rect())
        self.assertIsNotNone(g._trans_phase)

    def test_jumpscare_uses_packaged_art_without_scaling_each_frame(self):
        ui = self.game.ui
        self.assertIsNotNone(ui._jumpscare_sprite)
        self.assertEqual(len(ui._scare_frames), 4)
        self.assertTrue(all(frame.get_size() == (cfg.WIDTH, cfg.HEIGHT) for frame in ui._scare_frames))
        with patch("ui.pygame.transform.smoothscale", side_effect=AssertionError("escala em runtime")):
            for progress in (1, 0.75, 0.5, 0.25, 0.1, 0):
                ui.draw_jumpscare(self.screen, progress)


if __name__ == "__main__":
    unittest.main()
