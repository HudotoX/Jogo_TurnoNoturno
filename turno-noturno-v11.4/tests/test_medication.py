"""Regressões de pedidos, input real, derrota e uma noite completa sem janela."""
import os
import random
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import settings as cfg
from game import Game, STATE_PLAYING, STATE_NIGHT_END
from medication import MedicationManager, MEDICINES, Request
from patient import Patient
from shift_log import ShiftLog


class RequestRulesTests(unittest.TestCase):
    def setUp(self):
        self.patients = [Patient(1, "Paciente 01", "Ansiedade", cfg.PATIENT_ROOMS[0]),
                         Patient(2, "Paciente 02", "Percepção", cfg.PATIENT_ROOMS[2])]
        self.manager = MedicationManager(random.Random(1996))

    def begin(self):
        self.manager.update(20, 20, self.patients)
        return self.manager.active

    def test_first_request_is_guided_with_generous_deadline(self):
        self.assertIsNone(self.manager.update(19, 19, self.patients))
        self.assertIsNone(self.manager.active)
        self.manager.update(1, 20, self.patients)
        request = self.manager.active
        self.assertEqual((request.patient_id, request.required), (2, ("A",)))
        self.assertEqual(request.remaining, 70)
        self.assertTrue(self.patients[1].movement_locked)
        self.assertFalse(self.patients[1].move_to_random_room(cfg.CAMERAS))

    def test_tutorial_expiry_has_no_penalty_and_releases_movement(self):
        self.begin()
        self.manager.accept()
        self.manager.pick("A")
        self.manager.update(70, 90, self.patients)
        self.assertEqual(self.patients[1].stability, 100)
        self.assertFalse(self.patients[1].movement_locked)
        self.assertEqual(self.manager.tray, [])
        self.assertIsNone(self.manager.active)
        self.assertGreaterEqual(self.manager.next_in, cfg.REQUEST_INTERVAL_MIN)

    def test_exact_tray_and_single_reward(self):
        request = self.begin()
        self.assertFalse(self.manager.pick("A")[0])
        self.manager.accept()
        request.required = ("A", "C", "F")
        self.assertTrue(self.manager.pick("A")[0])
        self.assertFalse(self.manager.pick("A")[0])
        self.manager.pick("C")
        self.manager.pick("B")
        self.assertFalse(self.manager.pick("F")[0])
        patient = self.patients[1]
        patient.stability = 50
        self.assertFalse(self.manager.deliver(patient)[0])
        self.assertEqual(patient.stability, 50)
        self.manager.remove(2)
        self.manager.pick("F")
        self.assertFalse(self.manager.deliver(self.patients[0])[0])
        self.assertTrue(self.manager.deliver(patient)[0])
        self.assertEqual(patient.stability, 76)
        self.assertFalse(self.manager.deliver(patient)[0])
        self.assertEqual(self.manager.delivered, 1)
        self.assertEqual(self.manager.tray, [])

    def test_moderated_random_requests_and_distinct_items(self):
        self.begin()
        self.manager.update(70, 90, self.patients)
        wait = self.manager.next_in
        self.assertIsNone(self.manager.update(wait - 0.01, 100, self.patients))
        self.assertIsNone(self.manager.active)
        self.manager.update(0.02, 100.02, self.patients)
        self.assertIsNotNone(self.manager.active)
        sizes = set()
        for _ in range(80):
            request = self.manager.active
            sizes.add(len(request.required))
            self.assertEqual(len(request.required), len(set(request.required)))
            self.assertEqual(request.duration, cfg.REQUEST_SECONDS[len(request.required)])
            saved = request
            self.manager.update(0.1, 101, self.patients)
            self.assertIs(saved, self.manager.active)  # nenhum segundo pedido simultâneo
            self.manager.accept()
            self.manager.tray[:] = request.required
            self.manager.deliver(self.manager.patient(self.patients))
            self.manager.update(self.manager.next_in, 100, self.patients)
        self.assertEqual(sizes, {1, 2, 3})

    def test_expiry_cause_is_not_overwritten_by_later_drain(self):
        self.begin()
        self.manager.active.tutorial = False
        self.patients[1].stability = 15
        self.manager.update(70, 90, self.patients)
        self.patients[1].apply_loss(1, "other")
        self.assertIn("penalidade", self.patients[1].death_reason)
        self.assertEqual(self.manager.expired, 1)

    def test_no_impossible_request_at_end_of_night(self):
        self.manager.tutorial_started = True
        self.manager.next_in = 0
        self.manager.update(1, cfg.NIGHT_DURATION_SECONDS - 20, self.patients)
        self.assertIsNone(self.manager.active)

    def test_patients_never_enter_the_pharmacy(self):
        patient = self.patients[0]
        for _ in range(100):
            patient.move_to_random_room(cfg.CAMERAS)
            self.assertIn(patient.room, cfg.PATIENT_ROOMS)


class GameplayFlowTests(unittest.TestCase):
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
        self.game.state = STATE_PLAYING
        self.game.event_manager.events = []
        self.game.medication.rng.seed(17)
        self.random_patch = patch("patient.random.random", return_value=1)
        self.random_patch.start()

    def tearDown(self):
        self.random_patch.stop()
        self.game.audio.stop_ambient()

    def key(self, key):
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))

    def begin(self):
        self.game.update(20)
        self.key(pygame.K_F3)
        self.key(pygame.K_r)

    def test_keyboard_round_trip_wrong_item_and_repeat_delivery(self):
        g = self.game
        self.begin()
        self.assertTrue(g.medication.active.accepted)
        g.update(0.8)
        self.key(pygame.K_F5)
        self.key(pygame.K_w)  # B, pedido A
        self.assertEqual(g.medication.tray, ["B"])
        g.update(0.8)
        self.key(pygame.K_F3)
        self.key(pygame.K_r)
        self.assertIsNotNone(g.medication.active)
        self.assertIn("Confira", g.feedback)
        self.assertNotIn("relato", g.story.discovered)
        self.key(pygame.K_BACKSPACE)
        g.update(0.8)
        self.key(pygame.K_F5)
        self.key(pygame.K_q)
        g.update(0.8)
        self.key(pygame.K_F3)
        before = g.patients[1].stability
        self.key(pygame.K_r)
        self.assertIsNone(g.medication.active)
        self.assertAlmostEqual(g.patients[1].stability, before + 14)
        self.key(pygame.K_r)
        self.assertAlmostEqual(g.patients[1].stability, before + 14)
        self.assertEqual(g.medication.delivered, 1)
        self.assertEqual(g.story.discovered, ["relato"])

    def test_mouse_routes_match_drawn_buttons(self):
        g = self.game
        g.update(20)
        feed = g._playing_layout()[2]
        panel = g.ui.request_panel_rect(feed)
        def click(rect):
            g.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))
        click(g.ui.camera_tab_rects(5, cfg.TITLE_BAR_HEIGHT + 6)[2])
        click(g.ui.request_action_rect(panel))
        g.update(0.8)
        click(g.ui.camera_tab_rects(5, cfg.TITLE_BAR_HEIGHT + 6)[4])
        click(g.ui.pharmacy_item_rects(feed)[0])
        self.assertEqual(g.medication.tray, ["A"])
        click(g.ui.tray_rects(panel)[0])
        self.assertEqual(g.medication.tray, [])
        click(g.ui.pharmacy_item_rects(feed)[0])
        g.update(0.8)
        click(g.ui.camera_tab_rects(5, cfg.TITLE_BAR_HEIGHT + 6)[2])
        click(g.ui.request_action_rect(panel))
        self.assertEqual(g.medication.delivered, 1)

    def test_blackout_hidden_and_protocol_gate_interaction(self):
        g = self.game
        self.begin()
        request = g.medication.active
        request.tutorial = False
        g.patients[1].movement_locked = False
        g._try_start_protocol(1)
        self.assertIs(g.medication.active, request)
        before = request.remaining
        self.key(pygame.K_F5)
        self.assertEqual(g.camera_system.active_camera, "CAM 03")
        g._try_pick_medicine("A")
        self.assertEqual(g.medication.tray, [])
        g.update(1)
        self.assertAlmostEqual(request.remaining, before - 1)
        self.key(pygame.K_ESCAPE)
        g.camera_system.active_index = 4
        g.camera_system.trigger_blackout(3)
        g._try_pick_medicine("A")
        self.assertEqual(g.medication.tray, [])
        g.camera_system.blackout_timer = 0
        g._try_pick_medicine("A")
        g.camera_system.active_index = 2
        g.patients[1].is_hidden = True
        g._try_request_action()
        self.assertIs(g.medication.active, request)
        g.patients[1].is_hidden = False
        g._try_request_action()
        self.assertIsNone(g.medication.active)

    def test_patient_movement_requires_finding_current_camera(self):
        g = self.game
        self.begin()
        request = g.medication.active
        request.tutorial = False
        g.patients[1].movement_locked = False
        g.camera_system.active_index = 4
        g._try_pick_medicine("A")
        g.patients[1].room = "CAM 02"
        g.update(0.1)
        self.assertEqual(request.last_known_room, "CAM 03")
        g.camera_system.active_index = 2
        g._try_request_action()
        self.assertIsNotNone(g.medication.active)
        g.camera_system.active_index = 1
        g.update(0.1)
        self.assertEqual(request.last_known_room, "CAM 02")
        g._try_request_action()
        self.assertEqual(g.medication.delivered, 1)

    def test_successful_protocol_keeps_pending_request_and_tray(self):
        g = self.game
        self.begin()
        request = g.medication.active
        g.medication.tray = ["A"]
        g._try_start_protocol(1)
        with patch("game.pygame.key.get_pressed", return_value={pygame.K_SPACE: True}):
            g.update(4)
        self.assertIsNone(g.protocol_patient)
        self.assertIs(g.medication.active, request)
        self.assertEqual(g.medication.tray, ["A"])
        self.assertEqual(request.remaining, 66)
        self.assertEqual(g.patients[1].protocol_cooldown, 25)
        self.assertEqual(g.medication.delivered, 0)

    def test_protocol_close_button_cancels_without_losing_request_or_tray(self):
        g = self.game
        self.begin()
        request = g.medication.active
        g.medication.tray = ["A"]
        g._try_start_protocol(1)
        g.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                        pos=g.ui.protocol_close_rect().center))
        self.assertIsNone(g.protocol_patient)
        self.assertEqual(g.patients[1].protocol_cooldown, cfg.PROTOCOL_CANCEL_COOLDOWN_SECONDS)
        self.assertIs(g.medication.active, request)
        self.assertEqual(g.medication.tray, ["A"])

    def test_expiry_during_protocol_cannot_be_undone_by_completion(self):
        g = self.game
        self.begin()
        g.medication.active.tutorial = False
        g.medication.active.remaining = 1
        g.patients[1].stability = 10
        g._try_start_protocol(1)
        with patch("game.pygame.key.get_pressed", return_value={pygame.K_SPACE: True}):
            g.update(4)
        self.assertTrue(g.patients[1].is_lost())
        self.assertIn("penalidade", g.loss_report["causes"][0])
        self.assertIn("interrompido", g.loss_report["details"][0])

    def test_loss_report_preserves_expiry_and_cooldown(self):
        g = self.game
        self.begin()
        g.medication.active.tutorial = False
        g.medication.active.remaining = 0.1
        g.patients[1].stability = 10
        g.patients[1].protocol_cooldown = 8
        g.update(0.2)
        report = g.loss_report
        self.assertIn("Paciente 02", report["patients"])
        self.assertIn("penalidade", report["causes"][0])
        self.assertIn("recarga", report["details"][0])
        self.assertTrue(any("expirou" in e["text"] for e in report["events"]))
        self.assertEqual(report["expired"], 1)
        g.update(cfg.JUMPSCARE_DURATION)
        self.assertEqual(g.state, STATE_NIGHT_END)
        g.draw()
        g.start_night(1)
        self.assertIsNone(g.loss_report)
        self.assertEqual(len(g.shift_log.events), 0)
        self.assertIsNone(g.medication.active)

    def test_loss_during_protocol_has_precise_cause(self):
        g = self.game
        g.patients[0].stability = 0.1
        self.key(pygame.K_1)
        g.update(0.2)
        self.assertIn("durante o protocolo", g.loss_report["causes"][0])
        self.assertIn("interrompido", g.loss_report["details"][0])

    def test_complete_night_with_deliveries_protocols_and_scripted_events(self):
        # Piloto de integração usa input público e respeita o cooldown das câmeras.
        # Conhece a sala atual dos pacientes; não é uma prova de equilíbrio humano.
        from nights import NIGHT_1_EVENTS
        g = self.game
        g.event_manager.events = NIGHT_1_EVENTS
        with patch("game.pygame.key.get_pressed", return_value={pygame.K_SPACE: True}), \
             patch("game.savegame.save_progress"), patch("game.savegame.load_progress", return_value={"unlocked_night": 1}):
            for tick in range(3800):
                if tick % 4 == 0 and not g.protocol_patient and not g.jumpscare_timer and not g._trans_phase:
                    if g.story.pending_clue is not None:
                        self.key(pygame.K_f)
                    urgent = [p for p in g.patients if p.stability < 65 and p.can_start_protocol()]
                    request = g.medication.active
                    if urgent:
                        patient = min(urgent, key=lambda p: p.stability)
                        self.key(pygame.K_F1 + cfg.CAMERAS.index(patient.room))
                        if g._visible(patient):
                            self.key(pygame.K_1 + patient.id - 1)
                    elif request and (not request.accepted or g.medication.ready()):
                        patient = g.medication.patient(g.patients)
                        self.key(pygame.K_F1 + cfg.CAMERAS.index(patient.room))
                        self.key(pygame.K_r)
                    elif request:
                        self.key(pygame.K_F5)
                        if g.camera_system.active_camera == cfg.PHARMACY_CAMERA:
                            for med in MEDICINES:
                                if med.code in request.required and med.code not in g.medication.tray:
                                    self.key(ord(med.shortcut.lower()))
                                    break
                    else:
                        patient = min(g.patients, key=lambda p: p.stability)
                        self.key(pygame.K_F1 + cfg.CAMERAS.index(patient.room))
                g.update(0.1)
                if g.state == STATE_NIGHT_END:
                    break
        self.assertTrue(g.night_won, g.loss_report)
        self.assertGreaterEqual(g.medication.delivered, 5)
        self.assertEqual(g.event_manager._next_index, len(NIGHT_1_EVENTS))
        self.assertIsNone(g.loss_report)
        self.assertEqual(set(g.story.recorded), {"relato", "ficha", "falha"})
        self.assertIsNone(g.story.choice)
        # Completa o fade antes da escolha final por input público.
        g.update(cfg.SCENE_TRANSITION_SECONDS)
        self.key(pygame.K_RETURN)
        self.assertEqual(g.story.choice, "preserve")
        self.assertEqual(g.story.ending()[0], "UMA NOITE REGISTRADA")
        g.draw()


if __name__ == "__main__":
    unittest.main()
