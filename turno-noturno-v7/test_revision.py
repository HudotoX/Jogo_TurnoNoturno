"""Regressões: python -m unittest discover -s tests -v (sem NumPy)."""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import settings as cfg
from audio import AudioManager, SOUND_NAMES
from camera_system import CameraSystem
from game import Game, STATE_PLAYING
from patient import Patient


def new_patient():
    return Patient(1, "Paciente 01", "Ansiedade", cfg.CAMERAS[0])


class ProtocolTests(unittest.TestCase):
    def test_any_positive_stability_is_allowed(self):
        p = new_patient()
        for stability in (100, 90, 60, 26, 25, 10, 1):
            p.stability = stability
            self.assertTrue(p.can_start_protocol(), stability)
        p.stability = 0
        self.assertFalse(p.start_protocol())

    def test_success_cost_and_individual_cooldown(self):
        p = new_patient()
        p.stability = 50
        self.assertTrue(p.start_protocol())
        self.assertFalse(p.start_protocol())
        self.assertEqual(p.update_protocol(4, True), "success")
        self.assertAlmostEqual(p.stability, 96)
        self.assertEqual(p.protocol_cooldown, 25)
        self.assertFalse(p.can_start_protocol())
        self.assertTrue(new_patient().can_start_protocol())
        with patch("patient.random.random", return_value=1):
            p.update(25, True, cfg.CAMERAS)
        self.assertTrue(p.can_start_protocol())

    def test_recovery_is_capped(self):
        p = new_patient()
        p.stability = 90
        p.start_protocol()
        p.update_protocol(4, True)
        self.assertEqual(p.stability, cfg.STABILITY_MAX)

    def test_cancel_has_cost_but_no_recovery(self):
        p = new_patient()
        p.stability = 60
        p.start_protocol()
        p.update_protocol(1, True)
        p.cancel_protocol()
        self.assertEqual(p.stability, 59)
        self.assertEqual(p.protocol_cooldown, 6)
        self.assertFalse(p.can_start_protocol())

    def test_idle_protocol_does_not_advance_progress(self):
        p = new_patient()
        p.start_protocol()
        p.update_protocol(1, False)
        self.assertEqual(p.protocol_progress, 0)
        self.assertEqual(p.stability, 99)

    def test_protocol_can_still_fail_if_started_too_late(self):
        p = new_patient()
        p.stability = 3
        p.start_protocol()
        self.assertEqual(p.update_protocol(4, True), "failed")
        self.assertTrue(p.is_lost())

    def test_protocol_does_not_reveal_scripted_movement(self):
        p = new_patient()
        known = p.last_known_room
        p.start_protocol()
        p.room = cfg.CAMERAS[1]
        p.update_protocol(4, True)
        self.assertEqual(p.last_known_room, known)


class GameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.surface = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.game = Game(self.surface)
        self.game.start_night(1)
        self.game.state = STATE_PLAYING
        self.game.event_manager.events = []
        self.random_patch = patch("patient.random.random", return_value=1)
        self.random_patch.start()

    def tearDown(self):
        self.random_patch.stop()
        self.game.audio.stop_ambient()

    def test_visible_patient_starts_above_old_threshold(self):
        p = self.game.patients[0]
        p.stability = 70
        self.game._try_start_protocol(0)
        self.assertIs(self.game.protocol_patient, p)

    def test_blackout_hidden_wrong_room_and_cooldown_block(self):
        p = self.game.patients[0]
        p.stability = 70
        self.game.camera_system.blackout_timer = 3
        self.game._try_start_protocol(0)
        self.assertIsNone(self.game.protocol_patient)
        self.game.camera_system.blackout_timer = 0
        p.is_hidden = True
        self.game._try_start_protocol(0)
        self.assertIsNone(self.game.protocol_patient)
        p.is_hidden = False
        p.room = cfg.CAMERAS[2]
        self.game._try_start_protocol(0)
        self.assertIsNone(self.game.protocol_patient)
        p.room = cfg.CAMERAS[0]
        p.protocol_cooldown = 5
        self.game._try_start_protocol(0)
        self.assertIsNone(self.game.protocol_patient)

    def test_world_and_requests_advance_without_observation_bonus(self):
        g = self.game
        p1, p2 = g.patients
        p1.stability = 50
        p2.room = p1.room
        g.medication.next_in = 0
        g.medication.update(0, 20, g.patients)
        remaining = g.medication.active.remaining
        g._try_start_protocol(0)
        g.update(1)
        self.assertEqual(g.night_elapsed, 1)
        expected = 100 - cfg.DECAY_UNOBSERVED * 1.15
        self.assertAlmostEqual(p2.stability, expected)
        self.assertEqual(p2.seconds_since_seen, 1)
        self.assertAlmostEqual(g.medication.active.remaining, remaining - 1)
        self.assertAlmostEqual(p1.stability, 49)

    def test_success_frame_has_no_double_decay_or_cooldown_discount(self):
        p = self.game.patients[0]
        p.stability = 50
        self.game._try_start_protocol(0)
        with patch("game.pygame.key.get_pressed", return_value={pygame.K_SPACE: True}):
            self.game.update(4)
        self.assertIsNone(self.game.protocol_patient)
        self.assertAlmostEqual(p.stability, 96)
        self.assertEqual(p.protocol_cooldown, 25)

    def test_events_and_blackout_continue_during_protocol(self):
        g = self.game
        g._try_start_protocol(0)
        g.camera_system.trigger_blackout(3)
        g.event_manager.events = [{"time": 0.5, "type": "anomaly_sighting",
                                   "payload": {"patient_id": 2}}]
        g.update(1)
        self.assertEqual(g.camera_system.blackout_timer, 2)
        self.assertEqual(g.event_manager._next_index, 1)
        self.assertTrue(g.patients[1].is_glitched)
        self.assertIn("sombra", g.dialogue)

    def test_audio_and_all_render_states(self):
        g = self.game
        self.assertEqual(len(g.audio.sounds), len(SOUND_NAMES))
        self.assertTrue(all(sound is not None for sound in g.audio.sounds.values()))
        self.assertEqual(len(g.camera_system.bg_images), 4)
        self.assertEqual(len(g.camera_system.patient_images), 2)
        g.draw()
        g._try_start_protocol(0)
        g.draw()
        g.patients[0].cancel_protocol()
        g.protocol_patient = None
        g.draw()
        for image in g.camera_system.bg_images.values():
            r, green, b, _ = image.get_at(image.get_rect().center)
            self.assertEqual((r, green), (green, b))

    def test_no_audio_device_is_safe(self):
        with patch("audio.pygame.mixer.init", side_effect=pygame.error("test")):
            audio = AudioManager()
        self.assertFalse(audio.enabled)
        audio.start_ambient()
        audio.play_danger()
        audio.stop_ambient()

    def test_signal_glow_respects_low_opacity(self):
        camera = self.game.camera_system
        surface = pygame.Surface((20, 20))
        surface.fill((30, 30, 30))
        camera._draw_ambient_glow(surface, surface.get_rect(), cfg.CAMERAS[0])
        r, green, b, _ = surface.get_at((10, 10))
        self.assertLess(r, 45)  # não deve somar +150 e estourar os brancos
        self.assertEqual((r, green), (green, b))


if __name__ == "__main__":
    unittest.main()
