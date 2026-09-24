"""Controle por mouse do menu ao desfecho, incluindo gestos interrompidos."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import settings as cfg
from game import Game, STATE_MENU, STATE_NIGHT_INTRO, STATE_PLAYING, STATE_NIGHT_END
from main import _logical_mouse_event, _viewport
from medication import MEDICINES
from nights import NIGHT_1_EVENTS
from story import INTRO_PAGES


class MouseControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.keys = {pygame.K_SPACE: False}
        self.key_patch = patch("game.pygame.key.get_pressed", return_value=self.keys)
        self.key_patch.start()
        self.random_patch = patch("patient.random.random", return_value=1)
        self.random_patch.start()
        self.progress_patch = patch("game.savegame.save_progress")
        self.progress_patch.start()
        self.load_patch = patch("game.savegame.load_progress", return_value={"unlocked_night": 1})
        self.load_patch.start()
        self.g = Game(self.screen)
        # Janela com barras pretas: todo clique passa pela transformação real.
        self.view = _viewport((1280, 800))

    def tearDown(self):
        self.g.audio.stop_ambient()
        self.key_patch.stop()
        self.random_patch.stop()
        self.progress_patch.stop()
        self.load_patch.stop()
        pygame.event.clear()

    def pointer(self, event_type, pos, button=1):
        point = (self.view.left + round(pos[0] * self.view.width / cfg.WIDTH),
                 self.view.top + round(pos[1] * self.view.height / cfg.HEIGHT))
        event = pygame.event.Event(event_type, pos=point, button=button)
        self.g.handle_event(_logical_mouse_event(event, self.view))

    def click(self, rect):
        self.pointer(pygame.MOUSEBUTTONDOWN, rect.center)
        self.pointer(pygame.MOUSEBUTTONUP, rect.center)

    def transition(self):
        self.g.update(cfg.SCENE_TRANSITION_SECONDS)
        self.g.update(cfg.SCENE_TRANSITION_SECONDS)

    def start_playing(self):
        self.g.start_night(1)
        self.g.state = STATE_PLAYING
        self.g.event_manager.events = []
        self.g.medication.rng.seed(17)

    def open_protocol(self, index=0):
        panel_top = self.g._playing_layout()[1] - 130
        self.click(self.g.ui.patient_protocol_rects(len(self.g.patients), panel_top)[index])
        self.assertIs(self.g.protocol_patient, self.g.patients[index])

    def test_mouse_hold_releases_without_pausing_world_or_requests(self):
        self.start_playing()
        self.g.update(20)
        request = self.g.medication.active
        self.open_protocol()
        patient = self.g.protocol_patient
        hold = self.g.ui.protocol_hold_rect()
        self.pointer(pygame.MOUSEBUTTONDOWN, hold.center)
        before = request.remaining
        self.g.update(1)
        self.assertEqual(patient.protocol_progress, 1)
        self.pointer(pygame.MOUSEBUTTONUP, hold.center)
        self.g.update(1)
        self.assertEqual(patient.protocol_progress, 1)
        self.assertAlmostEqual(request.remaining, before - 2)
        self.assertEqual(self.g.night_elapsed, 22)
        self.pointer(pygame.MOUSEBUTTONDOWN, hold.center)
        self.g.update(cfg.PROTOCOL_HOLD_SECONDS - 1)
        self.assertIsNone(self.g.protocol_patient)
        self.assertEqual(patient.protocol_cooldown, cfg.PROTOCOL_COOLDOWN_SECONDS)
        self.assertFalse(self.g._protocol_mouse_held)

    def test_pointer_outside_button_requires_a_new_press(self):
        self.start_playing()
        self.open_protocol()
        patient = self.g.protocol_patient
        hold = self.g.ui.protocol_hold_rect()
        # Apertar fora e arrastar para dentro não inicia o gesto.
        self.pointer(pygame.MOUSEBUTTONDOWN, (hold.left - 8, hold.centery))
        self.pointer(pygame.MOUSEMOTION, hold.center)
        self.g.update(.25)
        self.assertEqual(patient.protocol_progress, 0)
        self.pointer(pygame.MOUSEBUTTONDOWN, hold.center)
        self.g.update(.5)
        self.pointer(pygame.MOUSEMOTION, (hold.right + 8, hold.centery))
        self.g.update(.5)
        self.pointer(pygame.MOUSEMOTION, hold.center)
        self.g.update(.5)
        self.assertEqual(patient.protocol_progress, .5)
        self.pointer(pygame.MOUSEBUTTONDOWN, hold.center)
        self.g.update(.5)
        self.assertEqual(patient.protocol_progress, 1)

    def test_focus_leave_resize_and_jumpscare_clear_hold(self):
        self.start_playing()
        self.open_protocol()
        patient = self.g.protocol_patient
        hold = self.g.ui.protocol_hold_rect()
        for event_type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWLEAVE,
                           pygame.WINDOWSIZECHANGED, pygame.WINDOWMINIMIZED):
            self.pointer(pygame.MOUSEBUTTONDOWN, hold.center)
            self.g.update(.1)
            progress = patient.protocol_progress
            self.g.handle_event(pygame.event.Event(event_type))
            self.g.update(.1)
            self.assertEqual(patient.protocol_progress, progress)
            self.g.handle_event(pygame.event.Event(pygame.WINDOWFOCUSGAINED))
        self.pointer(pygame.MOUSEBUTTONDOWN, hold.center)
        self.g.trigger_jumpscare()
        self.assertFalse(self.g._protocol_mouse_held)
        self.g.update(cfg.JUMPSCARE_DURATION)
        progress = patient.protocol_progress
        self.g.update(.2)
        self.assertEqual(patient.protocol_progress, progress)

    def test_cancel_button_has_same_cost_as_keyboard(self):
        self.start_playing()
        self.open_protocol()
        patient = self.g.protocol_patient
        self.pointer(pygame.MOUSEBUTTONDOWN, self.g.ui.protocol_hold_rect().center)
        self.g.update(.5)
        self.click(self.g.ui.protocol_cancel_rect())
        self.assertIsNone(self.g.protocol_patient)
        self.assertEqual(patient.protocol_cooldown, cfg.PROTOCOL_CANCEL_COOLDOWN_SECONDS)
        self.assertEqual(patient.protocol_progress, 0)
        self.assertFalse(self.g._protocol_mouse_held)

    def test_keyboard_and_mouse_together_do_not_double_progress(self):
        self.start_playing()
        self.open_protocol()
        patient = self.g.protocol_patient
        hold = self.g.ui.protocol_hold_rect()
        self.keys[pygame.K_SPACE] = True
        self.pointer(pygame.MOUSEBUTTONDOWN, hold.center)
        self.g.update(1)
        self.assertEqual(patient.protocol_progress, 1)
        self.pointer(pygame.MOUSEBUTTONUP, hold.center)
        self.g.update(1)
        self.assertEqual(patient.protocol_progress, 2)

    def test_mouse_screen_control_and_fixed_pixelation(self):
        self.click(self.g.ui.fullscreen_button_rect())
        self.assertTrue(self.g.fullscreen_requested)
        self.start_playing()
        for _ in range(3):
            self.g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F6))
        self.assertEqual(self.g.ui.pixelation.scale, .30)
        self.assertEqual(self.g.camera_system.pixelation.scale, .30)
        self.assertEqual([action for action, label in self.g.menu_options], ["continue", "quit"])
        self.g.draw()

    def test_loss_return_and_menu_close_are_clickable(self):
        self.g.state = STATE_NIGHT_END
        self.g.night_won = False
        self.click(pygame.Rect(0, 0, 4, 4))
        self.assertIsNone(self.g._trans_phase)
        self.click(self.g.ui.end_return_rect(False, False))
        self.transition()
        self.assertEqual(self.g.state, STATE_MENU)
        self.click(self.g.ui.menu_close_rect())
        self.assertTrue(any(e.type == pygame.QUIT for e in pygame.event.get()))

    def test_complete_night_uses_mouse_only_from_menu_to_ending(self):
        g = self.g
        self.click(g.ui.menu_option_rects(len(g.menu_options))[0])
        self.transition()
        self.assertEqual(g.state, STATE_NIGHT_INTRO)
        for page in range(len(INTRO_PAGES)):
            self.assertEqual(g.intro_page, page)
            advance = g.ui.intro_button_rects()[1]
            self.click(advance)  # revela
            self.assertTrue(g.ui.lore_fully_revealed())
            self.click(advance)  # avança
        self.transition()
        self.assertEqual(g.state, STATE_PLAYING)
        self.assertEqual(g.night_elapsed, 0)
        g.event_manager.events = NIGHT_1_EVENTS
        g.medication.rng.seed(17)
        feed = g._playing_layout()[2]
        panel = g.ui.request_panel_rect(feed)
        tabs = g.ui.camera_tab_rects(len(cfg.CAMERAS), cfg.TITLE_BAR_HEIGHT + 6)
        for tick in range(3800):
            if g.protocol_patient and not g.jumpscare_timer and not g._trans_phase:
                if not g._protocol_mouse_held:
                    self.pointer(pygame.MOUSEBUTTONDOWN, g.ui.protocol_hold_rect().center)
            elif tick % 4 == 0 and not g.jumpscare_timer and not g._trans_phase:
                if g.story.pending_clue is not None:
                    self.click(g.ui.record_button_rect(feed))
                urgent = [p for p in g.patients if p.stability < 65 and p.can_start_protocol()]
                request = g.medication.active
                if urgent:
                    patient = min(urgent, key=lambda p: p.stability)
                    self.click(tabs[cfg.CAMERAS.index(patient.room)])
                    if g._visible(patient):
                        self.open_protocol(patient.id - 1)
                elif request and (not request.accepted or g.medication.ready()):
                    patient = g.medication.patient(g.patients)
                    self.click(tabs[cfg.CAMERAS.index(patient.room)])
                    self.click(g.ui.request_action_rect(panel))
                elif request:
                    self.click(tabs[4])
                    if g.camera_system.active_camera == cfg.PHARMACY_CAMERA:
                        for index, medicine in enumerate(MEDICINES):
                            if medicine.code in request.required and medicine.code not in g.medication.tray:
                                self.click(g.ui.pharmacy_item_rects(feed)[index])
                                break
                else:
                    patient = min(g.patients, key=lambda p: p.stability)
                    self.click(tabs[cfg.CAMERAS.index(patient.room)])
            g.update(.1)
            if g.state == STATE_NIGHT_END:
                break
        self.assertTrue(g.night_won, g.loss_report)
        self.assertGreaterEqual(g.medication.delivered, 5)
        self.assertEqual(g.event_manager._next_index, len(NIGHT_1_EVENTS))
        self.assertEqual(set(g.story.recorded), {"relato", "ficha", "falha"})
        self.transition()
        self.click(g.ui.ending_record_rects()[0])
        self.assertEqual(g.story.review_key, "relato")
        self.click(g.ui.ending_choice_rects()[0])
        self.assertEqual(g.story.choice, "preserve")
        self.assertEqual(g.story.ending()[0], "UMA NOITE REGISTRADA")
        g.draw()
        self.click(g.ui.ending_return_rect())
        self.transition()
        self.assertEqual(g.state, STATE_MENU)
        self.click(g.ui.menu_option_rects(len(g.menu_options))[-1])
        self.assertTrue(any(e.type == pygame.QUIT for e in pygame.event.get()))


if __name__ == "__main__":
    unittest.main()
