"""
game.py
Máquina de estados principal do jogo (MENU, NIGHT_INTRO, PLAYING,
NIGHT_END) e orquestração dos demais sistemas (câmeras, pacientes,
eventos, áudio, UI). Não contém lógica de baixo nível de cada sistema
— apenas os conecta.
"""

import random
import pygame
import settings as cfg
import savegame
from camera_system import CameraSystem
from patient import Patient
from event_manager import EventManager
from audio import AudioManager
from ui import UI
from nights import EVENT_LOG_TEXT

STATE_MENU = "MENU"
STATE_NIGHT_INTRO = "NIGHT_INTRO"
STATE_PLAYING = "PLAYING"
STATE_NIGHT_END = "NIGHT_END"

FINAL_NIGHT = 1  # protótipo em foco: só a Noite 1 por enquanto (ver nights.py)


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.ui = UI()
        self.audio = AudioManager()

        self.state = STATE_MENU
        self.menu_selected = 0
        self.progress = savegame.load_progress()
        self.menu_options = self._build_menu_options()

        self.night_number = 1
        self.night_elapsed = 0.0
        self.night_won = False

        self.camera_system = None
        self.patients = []
        self.event_manager = None

        self.protocol_patient = None  # paciente atualmente em protocolo
        self.jumpscare_timer = 0.0
        self._pending_loss_after_jumpscare = False

        # superfície interna usada para poder "tremer" a tela durante o
        # jumpscare sem precisar redesenhar cada elemento com offset.
        self._scene_surface = pygame.Surface((cfg.WIDTH, cfg.HEIGHT))

        # transição fade-to-black entre cenas (menu <-> intro <-> jogo
        # <-> fim de noite). Ver _go_to()/_tick_transition().
        self._fade_surface = pygame.Surface((cfg.WIDTH, cfg.HEIGHT))
        self._fade_surface.fill((0, 0, 0))
        self._trans_phase = None   # None | "out" | "in"
        self._trans_timer = 0.0
        self._trans_next = None    # callable executado no meio da transição (tela preta)

    # ------------------------------------------------------------------
    def _build_menu_options(self):
        """Monta o menu dinamicamente conforme o progresso salvo:
        'Continuar' só aparece se já existe progresso além da Noite 1, e
        'Recomeçar do zero' só aparece se houver algo pra apagar. O clamp
        com FINAL_NIGHT evita mostrar uma noite que não existe mais nesta
        versão (ex.: um save antigo de quando havia Noite 2/3)."""
        unlocked = min(self.progress["unlocked_night"], FINAL_NIGHT)
        options = []
        if unlocked > 1:
            options.append(("continue", f"Continuar — Noite {unlocked}"))
            options.append(("restart", "Recomeçar do zero"))
        else:
            options.append(("continue", "Iniciar turno"))
        options.append(("quit", "Sair"))
        return options

    # ------------------------------------------------------------------
    def _go_to(self, setup):
        """Inicia uma transição de cena: escurece a tela, troca de estado
        no instante em que ela está totalmente preta (chamando `setup`),
        e clareia de volta revelando a cena nova. Usar isso em vez de
        atribuir `self.state` direto sempre que a mudança for algo que o
        jogador "sente" (menu -> noite, noite -> menu etc.)."""
        self._trans_phase = "out"
        self._trans_timer = 0.0
        self._trans_next = setup

    def _tick_transition(self, dt):
        """Retorna True se uma transição está em andamento (e portanto o
        resto de update() deve ser pulado nesse frame)."""
        if self._trans_phase is None:
            return False
        self._trans_timer += dt
        if self._trans_phase == "out" and self._trans_timer >= cfg.SCENE_TRANSITION_SECONDS:
            if self._trans_next is not None:
                self._trans_next()
                self._trans_next = None
            self._trans_phase = "in"
            self._trans_timer = 0.0
        elif self._trans_phase == "in" and self._trans_timer >= cfg.SCENE_TRANSITION_SECONDS:
            self._trans_phase = None
            self._trans_timer = 0.0
        return True

    def _transition_alpha(self):
        if self._trans_phase == "out":
            return int(255 * min(1.0, self._trans_timer / cfg.SCENE_TRANSITION_SECONDS))
        if self._trans_phase == "in":
            return int(255 * (1.0 - min(1.0, self._trans_timer / cfg.SCENE_TRANSITION_SECONDS)))
        return 0

    def _enter_menu(self):
        self.menu_options = self._build_menu_options()
        self.menu_selected = 0
        self.state = STATE_MENU

    def _enter_playing(self):
        self.state = STATE_PLAYING

    def _enter_night_end(self):
        self.state = STATE_NIGHT_END

    # ------------------------------------------------------------------
    def start_night(self, night_number):
        self.night_number = night_number
        self.night_elapsed = 0.0
        diff = cfg.NIGHT_DIFFICULTY.get(night_number, cfg.DEFAULT_DIFFICULTY)
        self.camera_system = CameraSystem(switch_cooldown_mult=diff["cam_switch_mult"])
        self.event_manager = EventManager(night_number)
        self.protocol_patient = None
        self.jumpscare_timer = 0.0
        self._pending_loss_after_jumpscare = False

        self.patients = [
            Patient(1, "Paciente 01", "Ansiedade", start_room=cfg.CAMERAS[0], profile="anxiety",
                    decay_mult=diff["decay_mult"], protocol_drain_mult=diff["protocol_drain_mult"],
                    call_window_mult=diff["call_window_mult"]),
            Patient(2, "Paciente 02", "Percepção", start_room=cfg.CAMERAS[2], profile="perception",
                    decay_mult=diff["decay_mult"], protocol_drain_mult=diff["protocol_drain_mult"],
                    call_window_mult=diff["call_window_mult"]),
        ]
        self.state = STATE_NIGHT_INTRO
        # zumbido/flicker + música baixinha já começam na tela de intro,
        # pra criar clima antes mesmo da noite "oficialmente" começar.
        self.audio.start_ambient()

    # ------------------------------------------------------------------
    def trigger_jumpscare(self, pending_loss=False):
        """Dispara o susto. Se pending_loss=True, o mundo fica congelado
        durante o susto e só checa derrota/vitória depois que ele acaba —
        cria o compasso 'SUSTO... aí sim a tela de derrota'."""
        self.jumpscare_timer = cfg.JUMPSCARE_DURATION
        self._pending_loss_after_jumpscare = pending_loss
        self.audio.play_jumpscare()

    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self._trans_phase is not None:
            return  # ignora entrada com a tela preta no meio da transição

        if self.state == STATE_MENU:
            self._handle_menu_input(event)
        elif self.state == STATE_NIGHT_INTRO:
            if event.key == pygame.K_RETURN:
                self._go_to(self._enter_playing)
        elif self.state == STATE_PLAYING:
            self._handle_playing_input(event)
        elif self.state == STATE_NIGHT_END:
            if event.key == pygame.K_RETURN:
                if self.night_won and self.night_number < FINAL_NIGHT:
                    self._go_to(lambda: self.start_night(self.night_number + 1))
                else:
                    self._go_to(self._enter_menu)

    def _handle_menu_input(self, event):
        n = len(self.menu_options)
        if event.key in (pygame.K_UP, pygame.K_w):
            self.menu_selected = (self.menu_selected - 1) % n
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.menu_selected = (self.menu_selected + 1) % n
        elif event.key == pygame.K_RETURN:
            action, _label = self.menu_options[self.menu_selected]
            if action == "continue":
                target_night = min(self.progress["unlocked_night"], FINAL_NIGHT)
                self._go_to(lambda: self.start_night(target_night))
            elif action == "restart":
                savegame.reset_progress()
                self.progress = savegame.load_progress()
                self.menu_options = self._build_menu_options()
                self._go_to(lambda: self.start_night(1))
            elif action == "quit":
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _handle_playing_input(self, event):
        if self.jumpscare_timer > 0:
            return  # entrada ignorada durante o susto

        if self.protocol_patient is not None:
            if event.key == pygame.K_ESCAPE:
                self.protocol_patient.cancel_protocol()
                self.protocol_patient = None
            return

        if event.key == pygame.K_ESCAPE:
            self.audio.stop_ambient()
            self._go_to(self._enter_menu)
            return

        if event.key in (pygame.K_RIGHT, pygame.K_d):
            if self.camera_system.next_camera():
                self.audio.play_camera_switch()
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            if self.camera_system.prev_camera():
                self.audio.play_camera_switch()
        elif event.key in (pygame.K_1, pygame.K_KP1):
            self._try_start_protocol(0)
        elif event.key in (pygame.K_2, pygame.K_KP2):
            self._try_start_protocol(1)
        elif event.key == pygame.K_r:
            self._try_answer_call()
        elif pygame.K_1 <= event.key <= pygame.K_4:
            idx = event.key - pygame.K_1
            if self.camera_system.switch_to(idx):
                self.audio.play_camera_switch()

    def _try_start_protocol(self, patient_index):
        if patient_index >= len(self.patients):
            return
        patient = self.patients[patient_index]
        if patient.can_start_protocol():
            patient.start_protocol()
            self.protocol_patient = patient

    def _try_answer_call(self):
        """Responde ao chamado do paciente que está na câmera ativa no
        momento — precisa estar realmente vendo a sala certa (câmera não
        pode estar em blecaute) pra contar."""
        if self.camera_system.is_blackout:
            return
        active_room = self.camera_system.active_camera
        for patient in self.patients:
            if patient.is_calling and patient.room == active_room:
                if patient.answer_call():
                    self.audio.play_call_answered()
                return

    # ------------------------------------------------------------------
    def _log(self, text):
        if text and self.event_manager is not None:
            self.event_manager.log_messages.append([text, 6.0])

    # ------------------------------------------------------------------
    def update(self, dt):
        self.ui.tick(dt)

        if self._tick_transition(dt):
            return  # mundo congelado enquanto a tela está fazendo fade

        if self.state != STATE_PLAYING:
            return

        # congela o mundo durante o susto (dá o compasso "SUSTO... e só
        # depois a consequência", em vez de tudo acontecer no mesmo frame)
        if self.jumpscare_timer > 0:
            self.jumpscare_timer = max(0.0, self.jumpscare_timer - dt)
            if self.jumpscare_timer == 0 and self._pending_loss_after_jumpscare:
                self._pending_loss_after_jumpscare = False
                self.night_won = False
                self.audio.stop_ambient()
                self.state = STATE_NIGHT_END
            return

        keys = pygame.key.get_pressed()

        if self.protocol_patient is not None:
            holding = keys[pygame.K_SPACE]
            result = self.protocol_patient.update_protocol(dt, holding)
            if result == "success":
                self.audio.play_protocol_success()
                self.protocol_patient = None
            elif result == "failed":
                self.protocol_patient = None
                self.trigger_jumpscare(pending_loss=True)
            return

        self.night_elapsed += dt
        self.camera_system.update(dt)

        active_room = self.camera_system.active_camera
        blackout = self.camera_system.is_blackout
        for patient in self.patients:
            being_observed = (patient.room == active_room) and not patient.is_hidden and not blackout
            events = patient.update(dt, being_observed, self.camera_system.cameras)
            for ev in events:
                if ev == "call_started":
                    self.audio.play_call_alert()
                    self._log(EVENT_LOG_TEXT.get("patient_call", ""))
                elif ev == "call_expired":
                    self.audio.play_call_expired()
                    self._log(EVENT_LOG_TEXT.get("call_expired", ""))
            if patient.state == cfg.STATE_PERIGO:
                self.audio.play_danger()

        self.event_manager.update(dt, self.night_elapsed, self.patients, self.camera_system, self.audio)
        if self.event_manager.consume_jumpscare_flag():
            self.trigger_jumpscare(pending_loss=False)

        # condição de derrota — mesmo susto, venha de uma falha de protocolo
        # ou de simplesmente deixar o paciente chegar a zero por negligência
        if any(p.is_lost() for p in self.patients):
            self.trigger_jumpscare(pending_loss=True)
            return

        # condição de vitória: sobreviveu até o fim da noite
        if self.night_elapsed >= cfg.NIGHT_DURATION_SECONDS:
            self.night_won = True
            self.audio.stop_ambient()
            savegame.save_progress(min(self.night_number + 1, FINAL_NIGHT))
            self.progress = savegame.load_progress()
            self._go_to(self._enter_night_end)

    # ------------------------------------------------------------------
    def draw(self):
        if self.state == STATE_MENU:
            self.ui.draw_menu(self.screen, self.menu_selected, self.menu_options)
        elif self.state == STATE_NIGHT_INTRO:
            self.ui.draw_night_intro(self.screen, self.night_number)
        elif self.state == STATE_PLAYING:
            self._draw_playing()
        elif self.state == STATE_NIGHT_END:
            self.ui.draw_end_screen(self.screen, self.night_won, self.night_number, FINAL_NIGHT)

        alpha = self._transition_alpha()
        if alpha > 0:
            self._fade_surface.set_alpha(alpha)
            self.screen.blit(self._fade_surface, (0, 0))

    def _draw_playing(self):
        target = self._scene_surface if self.jumpscare_timer > 0 else self.screen
        target.fill(cfg.COLOR_BG)

        feed_rect = pygame.Rect(20, 60, cfg.WIDTH - 40, cfg.HEIGHT - 220)
        flicker = self.event_manager.consume_flicker_flag() if self.jumpscare_timer == 0 else False
        self.camera_system.draw_feed(
            target, feed_rect, self.camera_system.active_camera,
            self.patients, self.ui.font_small, flicker=flicker)

        self.ui.draw_camera_tabs(target, self.camera_system)
        self.ui.draw_hud(target, self)
        self.ui.draw_call_banner(target, self)

        if flicker:
            self.ui.draw_light_flicker(target)

        if self.protocol_patient is not None:
            self.ui.draw_protocol_overlay(target, self.protocol_patient)

        if self.jumpscare_timer > 0:
            progress = self.jumpscare_timer / cfg.JUMPSCARE_DURATION
            self.ui.draw_jumpscare(target, progress)
            self._blit_with_shake(target, progress)

    def _blit_with_shake(self, scene, progress):
        magnitude = int(cfg.JUMPSCARE_SHAKE_MAGNITUDE * progress)
        offset_x = random.randint(-magnitude, magnitude) if magnitude > 0 else 0
        offset_y = random.randint(-magnitude, magnitude) if magnitude > 0 else 0
        self.screen.fill((0, 0, 0))
        self.screen.blit(scene, (offset_x, offset_y))
