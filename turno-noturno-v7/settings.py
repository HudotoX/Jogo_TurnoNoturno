"""
settings.py
Constantes globais e parâmetros de configuração do jogo.
Ajuste números aqui para reequilibrar o jogo sem tocar na lógica.
"""

# ---------- RESOLUÇÃO LÓGICA ----------
# main.py escala este canvas 16:9 para a janela/monitor disponível.
WIDTH, HEIGHT = 1920, 1080
FPS = 60
TITLE = "TURNO NOTURNO — Centro de Observação Clínica"

# ---------- CORES (placeholder art style) ----------
COLOR_BG = (10, 10, 14)
COLOR_PANEL = (18, 20, 26)
COLOR_PANEL_LIGHT = (28, 32, 40)
COLOR_TEXT = (210, 214, 220)
COLOR_TEXT_DIM = (120, 126, 136)
COLOR_ACCENT = (60, 200, 170)
COLOR_WARNING = (230, 180, 60)
COLOR_DANGER = (220, 70, 70)
COLOR_STATIC = (90, 90, 100)
COLOR_CAM_BORDER = (50, 55, 65)
COLOR_CAM_BORDER_ACTIVE = (60, 200, 170)

STATE_COLORS = {
    "NORMAL": (80, 190, 120),
    "INQUIETO": (220, 200, 70),
    "MOVENDO": (230, 150, 60),
    "ANORMAL": (200, 90, 190),
    "PERIGO": (220, 60, 60),
}

# ---------- CÂMERAS / SALAS ----------
PATIENT_ROOMS = ["CAM 01", "CAM 02", "CAM 03", "CAM 04"]
PHARMACY_CAMERA = "CAM 05"
CAMERAS = PATIENT_ROOMS + [PHARMACY_CAMERA]
ROOM_LABELS = {
    "CAM 01": "Ala de Descanso",
    "CAM 02": "Corredor Central",
    "CAM 03": "Sala de Observação",
    "CAM 04": "Pátio Interno",
    "CAM 05": "Ala Farmacêutica",
}

# ---------- ESTADOS DOS PACIENTES ----------
STATE_NORMAL = "NORMAL"
STATE_INQUIETO = "INQUIETO"
STATE_MOVENDO = "MOVENDO"
STATE_ANORMAL = "ANORMAL"
STATE_PERIGO = "PERIGO"

STATE_ORDER = [STATE_NORMAL, STATE_INQUIETO, STATE_MOVENDO, STATE_ANORMAL, STATE_PERIGO]

# Limiares de estabilidade (0-100) que definem o estado do paciente.
# Estabilidade ALTA = paciente bem. Estabilidade BAIXA = crise.
STATE_THRESHOLDS = {
    STATE_NORMAL: 76,     # stability >= 76
    STATE_INQUIETO: 51,   # 51-75
    STATE_MOVENDO: 26,    # 26-50
    STATE_ANORMAL: 11,    # 11-25
    STATE_PERIGO: 0,      # 0-10
}

# ---------- RITMO DA NOITE ----------
# Duração real (segundos) de uma noite jogável.
NIGHT_DURATION_SECONDS = 360  # 6 minutos reais
# Relógio in-game vai de 00:00 a 06:00.
NIGHT_START_HOUR = 0
NIGHT_END_HOUR = 6

# ---------- ESTABILIDADE ----------
STABILITY_MAX = 100
# Decaimento por segundo quando o paciente NÃO está sendo observado.
DECAY_UNOBSERVED = 1.65
# Decaimento por segundo quando ESTÁ sendo observado (observar acalma um pouco).
DECAY_OBSERVED = 0.62
# Chance por segundo (quando MOVENDO ou pior) de trocar de sala.
ROOM_CHANGE_CHANCE = 0.065
ROOM_CHANGE_COOLDOWN = 8.0  # tempo mínimo na mesma sala para poder localizar/entregar

# ---------- PROTOCOLO DE ESTABILIZAÇÃO ----------
PROTOCOL_HOLD_SECONDS = 4.0     # tempo segurando a tecla para completar
PROTOCOL_STABILITY_GAIN = 50    # quanto recupera ao concluir
PROTOCOL_RECOMMEND_THRESHOLD = 55  # apenas sugestão na HUD, NÃO bloqueia uso
# A estabilidade CONTINUA caindo durante o protocolo — se chegar a 0 antes de
# completar, é uma falha. Pode iniciar em qualquer estabilidade acima de zero,
# com o paciente visível. Valores de partida para playtest, não equilíbrio final.
PROTOCOL_DRAIN_RATE = 1.0       # 4 pontos ao completar em 4s (antes eram 15,6)
PROTOCOL_COOLDOWN_SECONDS = 25.0  # POR PACIENTE, contado a partir do sucesso
PROTOCOL_CANCEL_COOLDOWN_SECONDS = 6.0  # cancelar não recupera estabilidade

# ---------- CÂMERA: FRICÇÃO DE TROCA ----------
# Impede "pingue-pongar" entre câmeras instantaneamente todo frame.
CAMERA_SWITCH_COOLDOWN = 0.75

# ---------- ALARMES FALSOS ----------
# Eventos que parecem uma anomalia real (mesmo visual/som) mas custam pouca
# estabilidade de verdade — obrigam o jogador a checar a barra, não só reagir
# ao susto.
FALSE_ALARM_STABILITY_COST = 4

# ---------- BLECAUTE ----------
BLACKOUT_DURATION = 4.2

# ---------- JUMPSCARE ----------
JUMPSCARE_DURATION = 0.9
JUMPSCARE_SHAKE_MAGNITUDE = 16  # pixels

# ---------- TRANSIÇÕES DE CENA ----------
# Fade-to-black-e-volta entre menu/intro/jogo/fim de noite. Cada metade
# (escurecer, depois clarear) dura esse tanto; o mundo fica "congelado"
# durante a transição inteira.
SCENE_TRANSITION_SECONDS = 0.32

# ---------- ÁUDIO ----------
MASTER_VOLUME = 0.5
# Loops de atmosfera (audio.py: start_ambient/stop_ambient), já
# multiplicados por MASTER_VOLUME em runtime — mantidos bem baixos de
# propósito, é ruído de fundo, não efeito sonoro.
AMBIENT_HUM_VOLUME = 0.14     # zumbido/flicker elétrico contínuo
AMBIENT_MUSIC_VOLUME = 0.09   # "música" ambiente, bem baixinha

# ---------- FONTES ----------
FONT_NAME = None  # usa fonte padrão do sistema (pygame.font.SysFont)

# ---------- INTERCOMUNICADOR ("phone guy") ----------
# Mensagens de um coordenador de plantão que pontuam a noite — parte
# tutorial, parte construção de mundo. Ver nights.py (evento
# "intercom_message") e ui.py (draw_intercom, com efeito de máquina de
# escrever).
INTERCOM_CHAR_SECONDS = 0.028    # segundos por caractere revelado (velocidade da "digitação")
INTERCOM_HOLD_SECONDS = 4.5      # quanto tempo a mensagem fica na tela já revelada por completo
INTERCOM_SPEAKER_NAME = "T. ALMEIDA — COORDENAÇÃO"

# ---------- LORE DE ABERTURA DA NOITE ----------
# Texto exibido com efeito de máquina de escrever na tela de intro da
# noite (ver ui.py: start_night_lore/draw_night_intro). Segundos por
# caractere revelado — ENTER a qualquer momento revela tudo de uma vez.
LORE_CHAR_SECONDS = 0.026

# ---------- VISUAL "MONITOR VELHO" ----------
# Detalhes cosméticos aplicados por cima do HUD/câmeras durante o jogo
# pra dar a sensação de estar vendo tudo por um monitor CRT velho — sem
# mexer nas posições/tamanhos já calibrados de HUD e feed.
# ---------- VISUAL "PC ANTIGÃO" (estilo Windows 95) ----------
# Paleta e constantes do "chrome" de janela: barra de título, botões com
# relevo 3D, área de trabalho. Ver ui.py (draw_bevel_rect) pra como isso
# vira as bordas duplas clássicas.
# Paleta clássica do Windows 95 — cinza claro, barra de título azul.
WIN95_FACE = (192, 192, 192)         # cinza padrão de janelas/botões
WIN95_FACE_LIGHT = (223, 223, 223)   # variação clara (áreas de conteúdo)
WIN95_HILIGHT = (255, 255, 255)      # borda clara (relevo "pra fora")
WIN95_SHADOW = (128, 128, 128)       # borda escura média
WIN95_DARK_SHADOW = (0, 0, 0)        # borda escura externa
WIN95_TITLE_ACTIVE = (0, 0, 128)     # azul clássico da barra de título
WIN95_TITLE_TEXT = (255, 255, 255)
WIN95_DESKTOP_TEAL = (0, 128, 128)   # fundo clássico da área de trabalho
WIN95_TEXT = (10, 10, 10)
WIN95_TEXT_DIM = (90, 90, 90)
WIN95_SELECT_BLUE = (0, 0, 128)      # fundo de item "selecionado" numa lista

# ---------- LAYOUT DA "JANELA" DE JOGO ----------
TITLE_BAR_HEIGHT = 26
TASKBAR_HEIGHT = 34
MONITOR_BRAND = "CRT-9000 · SISTEMA VIGIA"

# ---------- SAVE / PROGRESSO ----------
# Guarda só a mais alta noite já desbloqueada (não um save "no meio da
# noite" — cada noite dura poucos minutos, não vale a pena salvar estado
# parcial). Perder a Noite 2 não te manda de volta pra Noite 1.
SAVE_FILE_NAME = "save_turno_noturno.json"

# ---------- DIFICULDADE POR NOITE ----------
# Multiplicadores aplicados sobre as constantes base acima, por noite —
# é isso que permite a Noite 2 ser mais apertada que a Noite 1 quando ela
# voltar, sem duplicar a lógica de balanceamento em cada lugar.
# Versão atual do jogo tem só a Noite 1 (protótipo em foco/polimento).
# Pra trazer a Noite 2/3 de volta: acrescentar a entrada aqui (ex.: `2: {...}`)
# + os eventos dela em nights.py (NIGHT_2_EVENTS, registrada em NIGHT_EVENTS)
# + subir FINAL_NIGHT em game.py.
NIGHT_DIFFICULTY = {
    1: {
        "decay_mult": 1.00,           # velocidade geral de deterioração
        "protocol_drain_mult": 1.00,  # risco de segurar o protocolo
        "cam_switch_mult": 1.00,      # fricção ao trocar de câmera
    },
}
DEFAULT_DIFFICULTY = {  # usado como fallback se alguma noite não estiver configurada acima
    "decay_mult": 1.5, "protocol_drain_mult": 1.4, "cam_switch_mult": 1.3,
}

# ---------- PEDIDOS / FARMÁCIA ----------
REQUEST_FIRST_AT = 20.0
REQUEST_TUTORIAL_SECONDS = 70.0
REQUEST_INTERVAL_MIN = 32.0  # contado APÓS resolver ou expirar o pedido anterior
REQUEST_INTERVAL_MAX = 48.0
REQUEST_SECONDS = {1: 30.0, 2: 40.0, 3: 50.0}
REQUEST_SIZE_WEIGHTS = (0.55, 0.30, 0.15)
REQUEST_STABILITY_GAIN = {1: 14, 2: 20, 3: 26}
REQUEST_EXPIRY_PENALTY = 18
TRAY_CAPACITY = 3

# ---------- VISUAL / ATMOSFERA ----------
# Estética fixa: 30% da largura E da altura da cena, ampliada sem filtro.
PIXEL_SCALE = 0.30
COLOR_BG_TOP = (8, 9, 13)
COLOR_BG_BOTTOM = (16, 18, 24)
COLOR_VIGNETTE = (0, 0, 0)
SCANLINE_ALPHA = 12          # linhas discretas sobre o sinal pixelizado
SCANLINE_SPACING = 3
# "Respiração" ambiente do sinal (ver camera_system._draw_ambient_glow) —
# neutro: não reintroduz cor depois de pygame.transform.grayscale().
CRT_GLOW_COLOR = (150, 150, 150)
MENU_GRID_COLOR = (22, 25, 32)

# ---------- PACIENTES NA CÂMERA (tamanho/proximidade) ----------
# É AQUI que você mexe pra mudar o tamanho dos pacientes na câmera.
# PATIENT_SPRITE_BASE_HEIGHT = altura-alvo (px) na câmera "padrão" (escala 1.0).
# Sobe esse número = todo mundo fica maior/mais perto em todas as câmeras.
PATIENT_SPRITE_BASE_HEIGHT = 650
# PATIENT_ROOM_SCALE = multiplicador por sala, em cima do valor acima —
# é o que faz a câmera do pátio parecer mais perto que a do corredor, por
# exemplo. 1.0 = tamanho padrão, >1.0 = mais perto/maior, <1.0 = mais longe.
# Obs.: o jogo nunca deixa o paciente ficar maior que o espaço disponível
# no quadro (ele encolhe sozinho se não couber), então pode subir esses
# números à vontade pra testar sem medo de cortar a cabeça de ninguém.
PATIENT_ROOM_SCALE = {
    "bed": 1.10,   # quarto — câmera relativamente próxima
    "hall": 0.80,  # corredor — plano mais aberto, câmera mais longe
    "desk": 0.95,  # sala de observação — distância média
    "yard": 0.7,  # pátio — câmera bem próxima do paciente
}
# É AQUI que você mexe pra subir/descer o boneco na tela (posição, não
# tamanho). Valor em pixels: NEGATIVO sobe o boneco, POSITIVO desce.
# 0 = em pé bem na linha do "chão" da sala.
PATIENT_ROOM_Y_OFFSET = {
    "bed": 690,
    "hall": 690,
    "desk": 690,
    "yard": 800,
}
# Escurecida uniforme aplicada por cima de TUDO (cenário + paciente) antes
# das scanlines/vinheta, pra integrar o paciente ao "sinal" da câmera em
# vez de parecer colado por cima.
SIGNAL_DIM_ALPHA = 34
