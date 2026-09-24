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
from medication import MedicationManager, MEDICINES
from shift_log import ShiftLog
from story import Story, INTRO_PAGES, CLUES, PATIENT_NAMES

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
        self.fullscreen_requested = False
        self._protocol_mouse_held = False
        self._mouse_pos = (-1, -1)
        self._input_focused = True

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
        self.medication = MedicationManager()
        self.shift_log = ShiftLog()
        self.loss_report = None
        self.feedback = ""
        self.feedback_timer = 0.0
        self.dialogue = ""
        self.dialogue_timer = 0.0
        self.story = Story()
        self.intro_page = 0

        self.protocol_patient = None  # paciente atualmente em protocolo
        self.jumpscare_timer = 0.0
        self._pending_loss_after_jumpscare = False
        self._danger_patient_ids = set()

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

    def release_mouse_hold(self):
        """Descarta o gesto ao soltar, trocar de tela ou sair da janela."""
        self._protocol_mouse_held = False

    def _holding_protocol(self, keys=None):
        if not self._input_focused:
            return False
        if keys is None:
            keys = pygame.key.get_pressed()
        # Usar os dois controles ao mesmo tempo nunca acelera o protocolo.
        return bool(keys[pygame.K_SPACE] or self._protocol_mouse_held)

    # ------------------------------------------------------------------
    def _go_to(self, setup):
        """Inicia uma transição de cena: escurece a tela, troca de estado
        no instante em que ela está totalmente preta (chamando `setup`),
        e clareia de volta revelando a cena nova. Usar isso em vez de
        atribuir `self.state` direto sempre que a mudança for algo que o
        jogador "sente" (menu -> noite, noite -> menu etc.)."""
        self.release_mouse_hold()
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

    def _show_intro_page(self, page):
        self.intro_page = max(0, min(len(INTRO_PAGES) - 1, page))
        self.ui.start_night_lore(INTRO_PAGES[self.intro_page]["text"])

    def _advance_intro(self):
        if not self.ui.lore_fully_revealed():
            self.ui.skip_lore()
        elif self.intro_page < len(INTRO_PAGES) - 1:
            self._show_intro_page(self.intro_page + 1)
        else:
            self._go_to(self._enter_playing)

    def _choose_ending(self):
        choice = ("preserve", "automatic")[self.story.ending_selected]
        if self.story.choose(choice):
            self.audio.play_blip()

    def _handle_ending_input(self, event):
        if self.night_won and self.story.choice is None:
            if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                self.story.ending_selected = 1 - self.story.ending_selected
            elif event.key == pygame.K_RETURN:
                self._choose_ending()
        elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            self._go_to(self._enter_menu)

    def _handle_ending_click(self, pos):
        if not self.night_won:
            if (self.ui.end_return_rect(False, bool(self.loss_report)).collidepoint(pos)
                    or self.ui.end_close_rect(False, bool(self.loss_report)).collidepoint(pos)):
                self._go_to(self._enter_menu)
        elif self.story.choice is None:
            for key, rect in zip(CLUES, self.ui.ending_record_rects()):
                if key in self.story.recorded and rect.collidepoint(pos):
                    self.story.review_key = key
                    return
            for index, rect in enumerate(self.ui.ending_choice_rects()):
                if rect.collidepoint(pos):
                    self.story.ending_selected = index
                    self._choose_ending()
                    return
        elif (self.ui.ending_return_rect().collidepoint(pos)
              or self.ui.story_close_rect().collidepoint(pos)):
            self._go_to(self._enter_menu)

    # ------------------------------------------------------------------
    def start_night(self, night_number):
        self.night_number = night_number
        self.night_elapsed = 0.0
        diff = cfg.NIGHT_DIFFICULTY.get(night_number, cfg.DEFAULT_DIFFICULTY)
        self.camera_system = CameraSystem(switch_cooldown_mult=diff["cam_switch_mult"])
        self.event_manager = EventManager(night_number)
        self.release_mouse_hold()
        self.protocol_patient = None
        self.jumpscare_timer = 0.0
        self._pending_loss_after_jumpscare = False
        self._danger_patient_ids = set()

        self.patients = [
            Patient(1, "Paciente 01", "Ansiedade", start_room=cfg.CAMERAS[0], profile="anxiety",
                    decay_mult=diff["decay_mult"], protocol_drain_mult=diff["protocol_drain_mult"]),
            Patient(2, "Paciente 02", "Percepção", start_room=cfg.CAMERAS[2], profile="perception",
                    decay_mult=diff["decay_mult"], protocol_drain_mult=diff["protocol_drain_mult"]),
        ]
        self.medication = MedicationManager()
        self.shift_log = ShiftLog()
        self.loss_report = None
        self.night_won = False
        self.feedback = self.dialogue = ""
        self.feedback_timer = self.dialogue_timer = 0.0
        self.story = Story()
        self.state = STATE_NIGHT_INTRO
        self._show_intro_page(0)
        # zumbido/flicker + música baixinha já começam na tela de intro,
        # pra criar clima antes mesmo da noite "oficialmente" começar.
        self.audio.start_ambient()

    # ------------------------------------------------------------------
    def trigger_jumpscare(self, pending_loss=False):
        """Dispara o susto. Se pending_loss=True, o mundo fica congelado
        durante o susto e só checa derrota/vitória depois que ele acaba —
        cria o compasso 'SUSTO... aí sim a tela de derrota'."""
        self.release_mouse_hold()
        self.jumpscare_timer = cfg.JUMPSCARE_DURATION
        self._pending_loss_after_jumpscare = pending_loss
        self.audio.play_jumpscare()

    # ------------------------------------------------------------------
    def handle_event(self, event):
        # Processa liberações antes de qualquer bloqueio de input: um mouse
        # solto durante fade/susto não pode ficar preso no próximo protocolo.
        if event.type == pygame.WINDOWFOCUSLOST:
            self._input_focused = False
            self.release_mouse_hold()
            return
        if event.type == pygame.WINDOWFOCUSGAINED:
            self._input_focused = True
            return
        if event.type in (pygame.WINDOWLEAVE, pygame.WINDOWMINIMIZED,
                          pygame.WINDOWRESIZED, pygame.WINDOWSIZECHANGED):
            self.release_mouse_hold()
            return
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.release_mouse_hold()
            return
        if event.type == pygame.MOUSEMOTION:
            self._mouse_pos = event.pos
            if not self.ui.protocol_hold_rect().collidepoint(event.pos):
                self.release_mouse_hold()
            return
        if event.type not in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            return
        if self._trans_phase is not None or not self._input_focused:
            return  # ignora entrada com a tela preta no meio da transição

        if event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_mouse_click(event)
            return

        if self.state == STATE_MENU:
            self._handle_menu_input(event)
        elif self.state == STATE_NIGHT_INTRO:
            if event.key == pygame.K_RETURN:
                self._advance_intro()
            elif event.key == pygame.K_LEFT and self.intro_page > 0:
                self._show_intro_page(self.intro_page - 1)
            elif event.key == pygame.K_ESCAPE:
                self.audio.stop_ambient()
                self._go_to(self._enter_menu)
        elif self.state == STATE_PLAYING:
            self._handle_playing_input(event)
        elif self.state == STATE_NIGHT_END:
            self._handle_ending_input(event)

    # ------------------------------------------------------------------
    def _handle_mouse_click(self, event):
        if event.button != 1:
            return  # só o botão esquerdo interage; direito/meio ignorados
        self._mouse_pos = event.pos
        if ((self.state != STATE_PLAYING or
             (self.jumpscare_timer <= 0 and self.protocol_patient is None))
                and self.ui.fullscreen_button_rect().collidepoint(event.pos)):
            self.fullscreen_requested = True
            return

        if self.state == STATE_MENU:
            self._handle_menu_click(event.pos)
        elif self.state == STATE_NIGHT_INTRO:
            back, advance = self.ui.intro_button_rects()
            if self.ui.story_close_rect().collidepoint(event.pos):
                self.audio.stop_ambient()
                self._go_to(self._enter_menu)
            elif back.collidepoint(event.pos) and self.intro_page > 0:
                self._show_intro_page(self.intro_page - 1)
            elif advance.collidepoint(event.pos):
                self._advance_intro()
            elif not self.ui.lore_fully_revealed():
                self.ui.skip_lore()
        elif self.state == STATE_PLAYING:
            self._handle_playing_click(event.pos)
        elif self.state == STATE_NIGHT_END:
            self._handle_ending_click(event.pos)

    def _handle_menu_click(self, pos):
        if self.ui.menu_close_rect().collidepoint(pos):
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return
        rects = self.ui.menu_option_rects(len(self.menu_options))
        for i, rect in enumerate(rects):
            if rect.collidepoint(pos):
                self.menu_selected = i
                action, _label = self.menu_options[i]
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
                return

    def _handle_playing_click(self, pos):
        _content_top, _content_bottom, _feed_rect, close_btn = self._playing_layout()

        if self.jumpscare_timer > 0:
            return
        if self.protocol_patient is not None:
            if (self.ui.protocol_close_rect().collidepoint(pos)
                    or self.ui.protocol_cancel_rect().collidepoint(pos)):
                self._cancel_protocol()
            elif self.ui.protocol_hold_rect().collidepoint(pos):
                self._protocol_mouse_held = True
            return

        if close_btn.collidepoint(pos):
            if self.protocol_patient is None and self.jumpscare_timer == 0:
                self.audio.stop_ambient()
                self._go_to(self._enter_menu)
            return

        if self.story.pending_clue is not None and self.ui.record_button_rect(_feed_rect).collidepoint(pos):
            self._try_record_clue()
            return

        # 1) abas de câmera
        tab_rects = self.ui.camera_tab_rects(len(self.camera_system.cameras), top=_content_top + 6)
        for i, rect in enumerate(tab_rects):
            if rect.collidepoint(pos):
                if self.camera_system.switch_to(i):
                    self.audio.play_camera_switch()
                return

        # 2) Pedido, bandeja e prateleiras compartilham a geometria do desenho.
        panel = self.ui.request_panel_rect(_feed_rect)
        if self.ui.request_action_rect(panel).collidepoint(pos):
            self._try_request_action()
            return
        for index, rect in enumerate(self.ui.tray_rects(panel)):
            if rect.collidepoint(pos):
                self._remove_medicine(index)
                return
        if self.camera_system.active_camera == cfg.PHARMACY_CAMERA:
            for medicine, rect in zip(MEDICINES, self.ui.pharmacy_item_rects(_feed_rect)):
                if rect.collidepoint(pos):
                    self._try_pick_medicine(medicine.code)
                    return

        # 3) barra de estabilidade de um paciente — clicar nela tenta
        # iniciar o protocolo. A câmera precisa estar mostrando o paciente.
        panel_top = _content_bottom - 130
        bar_rects = self.ui.stability_bar_rects(len(self.patients), panel_top)
        buttons = self.ui.patient_protocol_rects(len(self.patients), panel_top)
        for i, (rect, button) in enumerate(zip(bar_rects, buttons)):
            hit_zone = rect.inflate(0, 40)  # facilita o clique, não precisa acertar a barrinha fina
            if hit_zone.collidepoint(pos) or button.collidepoint(pos):
                self._try_start_protocol(i)
                return

    def _handle_menu_input(self, event):
        n = len(self.menu_options)
        if event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        elif event.key in (pygame.K_UP, pygame.K_w):
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
                self._cancel_protocol()
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
            self._try_request_action()
        elif event.key == pygame.K_f:
            self._try_record_clue()
        elif event.key == pygame.K_BACKSPACE:
            self._remove_medicine(len(self.medication.tray) - 1)
        elif pygame.K_F1 <= event.key <= pygame.K_F5:
            idx = event.key - pygame.K_F1
            if self.camera_system.switch_to(idx):
                self.audio.play_camera_switch()
        else:
            for medicine in MEDICINES:
                if event.key == ord(medicine.shortcut.lower()):
                    self._try_pick_medicine(medicine.code)
                    break

    def _cancel_protocol(self):
        self.release_mouse_hold()
        patient = self.protocol_patient
        if patient is None:
            return
        self._log(f"{patient.name}: protocolo cancelado, "
                  f"recarga de {cfg.PROTOCOL_CANCEL_COOLDOWN_SECONDS:g}s.", patient.id)
        patient.cancel_protocol()
        self.protocol_patient = None

    def _try_start_protocol(self, patient_index):
        if (self.protocol_patient is not None or self.jumpscare_timer > 0
                or not 0 <= patient_index < len(self.patients)):
            return
        patient = self.patients[patient_index]
        visible_now = (not self.camera_system.is_blackout
                       and not patient.is_hidden
                       and patient.room == self.camera_system.active_camera)
        if visible_now and patient.start_protocol():
            self.release_mouse_hold()
            self.protocol_patient = patient
            self._log(f"{patient.name}: protocolo iniciado com {patient.stability:.0f} de estabilidade.", patient.id)
        elif not visible_now:
            self._feedback("Abra a câmera do paciente para iniciar o protocolo.")
        elif patient.protocol_cooldown > 0:
            self._feedback(f"Protocolo em recarga: {patient.protocol_cooldown:.0f}s.")

    def _can_interact(self):
        return (self.state == STATE_PLAYING and self.protocol_patient is None
                and self.jumpscare_timer <= 0 and self._trans_phase is None)

    def _visible(self, patient):
        return (patient is not None and not patient.is_lost() and not patient.is_hidden
                and not self.camera_system.is_blackout
                and patient.room == self.camera_system.active_camera)

    def _try_request_action(self):
        if not self._can_interact():
            return
        patient = self.medication.patient(self.patients)
        if patient is None:
            self._feedback("Nenhum pedido pendente. Continue observando os pacientes.")
            return
        if not self._visible(patient):
            self._feedback(f"Localize {patient.name} em uma câmera com sinal.")
            return
        request = self.medication.active
        if not request.accepted:
            self.medication.accept()
            self.audio.play_call_answered()
            self._log(f"{patient.name}: pedido anotado ({', '.join(request.required)}).", patient.id)
            self._say(patient.id, "Vou esperar. Só não demore, por favor.", important=False)
            self._feedback("Pedido anotado. Abra a aba Farmácia (F5).")
        else:
            success, message = self.medication.deliver(patient)
            self._feedback(message)
            if success:
                self.audio.play_call_answered()
                self._log(f"{patient.name}: {message}", patient.id)
                if not self.story.on_delivery(patient.id):
                    self._say(patient.id, "Obrigado por voltar. Já me sinto um pouco melhor.", important=False)

    def _try_pick_medicine(self, code):
        if not self._can_interact():
            return
        if self.camera_system.active_camera != cfg.PHARMACY_CAMERA:
            self._feedback("Os medicamentos ficam na aba Farmácia (F5).")
            return
        if self.camera_system.is_blackout:
            self._feedback("Sem sinal na farmácia. Aguarde o retorno das câmeras.")
            return
        success, message = self.medication.pick(code)
        self._feedback(message)
        if success:
            self.audio.play_blip()

    def _remove_medicine(self, index):
        if self._can_interact() and self.medication.remove(index):
            self.audio.play_blip()
            self._feedback("Item removido da bandeja.")

    def _feedback(self, text):
        self.feedback = text
        self.feedback_timer = 6.0

    def _say(self, patient_id, text, important=True):
        self.dialogue = f'Paciente {patient_id:02d}: “{text}”'
        self.dialogue_timer = 9.0
        name = PATIENT_NAMES.get(patient_id, f"Paciente {patient_id:02d}")
        self.story.say(f"{name.upper()} · PACIENTE {patient_id:02d}", text, important=important)

    def _try_record_clue(self):
        if not self._can_interact():
            return
        key = self.story.record_next()
        if key is None:
            self._feedback("Ainda não há uma nova descoberta para guardar.")
            return
        text = f"Registro guardado: {CLUES[key]['title']}."
        self._feedback(text)
        self._log(text)
        self.audio.play_blip()

    # ------------------------------------------------------------------
    def _log(self, text, patient_id=None):
        if text and self.event_manager is not None:
            self.event_manager.log_messages.append([text, 6.0])
            self.shift_log.record(self.night_elapsed, text, patient_id)

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
        self.feedback_timer = max(0.0, self.feedback_timer - dt)
        self.dialogue_timer = max(0.0, self.dialogue_timer - dt)

        # Atualiza primeiro o mundo: ao concluir o protocolo neste frame, não
        # cobra também o decaimento normal nem desconta do cooldown recém-criado.
        protocol_active = self.protocol_patient is not None
        self.night_elapsed += dt
        self.camera_system.update(dt)

        active_room = self.camera_system.active_camera
        blackout = self.camera_system.is_blackout
        for patient in self.patients:
            being_observed = (not protocol_active and patient.room == active_room
                              and not patient.is_hidden and not blackout)
            events = patient.update(dt, being_observed, cfg.PATIENT_ROOMS)
            for ev in events:
                if ev == "moved":
                    self._log(f"{patient.name} mudou de sala.", patient.id)
        self.event_manager.update(dt, self.night_elapsed, self.patients, self.camera_system, self.audio)
        if self.camera_system.is_blackout:
            self.story.on_blackout()
        for text, patient_id in self.event_manager.records:
            self.shift_log.record(self.night_elapsed, text, patient_id)
        self.event_manager.records.clear()
        for patient_id, text in self.event_manager.dialogues:
            self._say(patient_id, text)
        self.event_manager.dialogues.clear()

        request_event = self.medication.update(dt, self.night_elapsed, self.patients)
        if request_event:
            pid = request_event["patient_id"]
            self._log(f"Paciente {pid:02d}: {request_event['text']}", pid)
            if request_event["kind"] == "started":
                self.audio.play_call_alert()
            else:
                self.audio.play_call_expired()
                self._feedback(request_event["text"])

        # Depois dos movimentos/eventos, atualiza só informações que a câmera mostra.
        request = self.medication.active
        for patient in self.patients:
            if not protocol_active and self._visible(patient):
                patient.refresh_reading()
                if request is not None and request.patient_id == patient.id:
                    request.last_known_room = patient.room

        if self.protocol_patient is not None:
            result = self.protocol_patient.update_protocol(dt, self._holding_protocol(keys))
            if result == "success":
                self.audio.play_protocol_success()
                self._log(f"{self.protocol_patient.name}: protocolo concluído; "
                          f"recarga de {cfg.PROTOCOL_COOLDOWN_SECONDS:g}s.",
                          self.protocol_patient.id)
                self.protocol_patient = None
                self.release_mouse_hold()
            elif result == "failed":
                self.protocol_patient = None
                self.release_mouse_hold()

        danger_now = {p.id for p in self.patients if p.state == cfg.STATE_PERIGO}
        if danger_now - self._danger_patient_ids:
            self.audio.play_danger()
            for patient in self.patients:
                if patient.id in danger_now - self._danger_patient_ids:
                    self.shift_log.record(self.night_elapsed,
                                          f"{patient.name}: estabilidade entrou em nível crítico.", patient.id)
        self._danger_patient_ids = danger_now

        # condição de derrota — mesmo susto, venha de uma falha de protocolo
        # ou de simplesmente deixar o paciente chegar a zero por negligência
        if any(p.is_lost() for p in self.patients):
            self.loss_report = self.shift_log.loss_report(self.patients, self.night_elapsed, self.medication)
            self.trigger_jumpscare(pending_loss=True)
            return

        if self.event_manager.consume_jumpscare_flag():
            self.trigger_jumpscare(pending_loss=False)

        self.story.observe(self.night_elapsed, self.camera_system.active_camera,
                           self.camera_system.is_blackout, self._can_interact())
        self.story.update(dt, self.night_elapsed,
                          can_read=not protocol_active and self.jumpscare_timer <= 0)

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
            self.ui.draw_story_intro(self.screen, self.intro_page)
        elif self.state == STATE_PLAYING:
            self._draw_playing()
        elif self.state == STATE_NIGHT_END:
            if self.night_won:
                self.ui.draw_story_ending(self.screen, self.story, self.medication.delivered)
            else:
                self.ui.draw_end_screen(self.screen, False, self.night_number, FINAL_NIGHT,
                                        self.loss_report, self.medication.delivered)

        alpha = self._transition_alpha()
        if alpha > 0:
            self._fade_surface.set_alpha(alpha)
            self.screen.blit(self._fade_surface, (0, 0))

    def _playing_layout(self):
        """Geometria da 'janela' de jogo (barra de título, taskbar, feed)
        — usada tanto por _draw_playing quanto pelo clique do mouse, pra
        nunca ficarem dessincronizadas."""
        content_top = cfg.TITLE_BAR_HEIGHT
        content_bottom = cfg.HEIGHT - cfg.TASKBAR_HEIGHT
        feed_top = content_top + 46
        feed_rect = pygame.Rect(20, feed_top, cfg.WIDTH - 484, content_bottom - 150 - feed_top)
        close_btn = pygame.Rect(cfg.WIDTH - 24, 4, 18, 18)
        return content_top, content_bottom, feed_rect, close_btn

    def _draw_playing(self):
        target = self._scene_surface if self.jumpscare_timer > 0 else self.screen
        target.fill(cfg.WIN95_DESKTOP_TEAL)

        # ---------- "janela" do programa de vigilância (maximizada) ----------
        # Barra de título fixa no topo da tela e barra de tarefas fixa no
        # rodapé — tudo que já existia (abas, feed, HUD) fica encaixado
        # no espaço entre as duas, sem mudar a lógica de nada, só onde é
        # desenhado. _playing_layout() centraliza os números, pro clique
        # do mouse usar exatamente os mesmos.
        content_top, content_bottom, feed_rect, close_btn = self._playing_layout()

        title_bar = pygame.Rect(0, 0, cfg.WIDTH, content_top)
        pygame.draw.rect(target, cfg.WIN95_TITLE_ACTIVE, title_bar)

        icon_rect = pygame.Rect(6, 4, 18, 18)
        pygame.draw.rect(target, cfg.WIN95_FACE, icon_rect)
        pygame.draw.rect(target, cfg.WIN95_DARK_SHADOW, icon_rect, 1)

        title_txt = self.ui.font_medium.render(f"VIGIA.EXE — Noite {self.night_number}", True, cfg.WIN95_TITLE_TEXT)
        target.blit(title_txt, (icon_rect.right + 6, title_bar.centery - title_txt.get_height() // 2))

        self.ui.draw_bevel_rect(target, close_btn, raised=True)
        x_txt = self.ui.font_small.render("X", True, cfg.WIN95_TEXT)
        target.blit(x_txt, (close_btn.centerx - x_txt.get_width() // 2, close_btn.centery - x_txt.get_height() // 2 - 1))

        self.ui.draw_taskbar(target)

        flicker = self.event_manager.consume_flicker_flag() if self.jumpscare_timer == 0 else False
        self.camera_system.draw_feed(
            target, feed_rect, self.camera_system.active_camera,
            self.patients, self.ui.font_small, flicker=flicker)

        self.ui.draw_camera_tabs(target, self.camera_system, top=content_top + 6)
        self.ui.draw_hud(target, self, panel_bottom=content_bottom)
        if self.camera_system.active_camera == cfg.PHARMACY_CAMERA:
            self.ui.draw_pharmacy(target, self, feed_rect)
        self.ui.draw_request_panel(target, self, self.ui.request_panel_rect(feed_rect))
        self.ui.draw_story_strip(target, self, feed_rect)

        if flicker:
            self.ui.draw_light_flicker(target)

        if self.protocol_patient is not None:
            self.ui.draw_protocol_overlay(target, self.protocol_patient,
                                           holding=self._holding_protocol())
            self.ui.draw_protocol_request_hint(target, self.medication.active)

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
