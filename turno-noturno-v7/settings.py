"""
settings.py
Constantes globais e parâmetros de configuração do jogo.
Ajuste números aqui para reequilibrar o jogo sem tocar na lógica.
"""

# ---------- JANELA ----------
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
CAMERAS = ["CAM 01", "CAM 02", "CAM 03", "CAM 04"]
ROOM_LABELS = {
    "CAM 01": "Ala de Descanso",
    "CAM 02": "Corredor Central",
    "CAM 03": "Sala de Observação",
    "CAM 04": "Pátio Interno",
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
DECAY_UNOBSERVED = 1.35
# Decaimento por segundo quando ESTÁ sendo observado (observar acalma um pouco).
DECAY_OBSERVED = 0.55
# Chance por segundo (quando MOVENDO ou pior) de trocar de sala.
ROOM_CHANGE_CHANCE = 0.05

# ---------- PROTOCOLO DE ESTABILIZAÇÃO ----------
PROTOCOL_HOLD_SECONDS = 4.0     # tempo segurando a tecla para completar
PROTOCOL_STABILITY_GAIN = 55    # quanto recupera ao concluir
PROTOCOL_TRIGGER_THRESHOLD = 25  # abaixo disso, protocolo fica disponível/recomendado
# A estabilidade CONTINUA caindo durante o protocolo — se chegar a 0 antes de
# completar, é uma falha (dispara jumpscare). Acionar cedo demais é seguro;
# deixar chegar quase no fundo antes de agir agora é arriscado de verdade.
PROTOCOL_DRAIN_RATE = 3.2
PROTOCOL_COOLDOWN_SECONDS = 6.0        # espera antes de poder reaplicar após sucesso
PROTOCOL_CANCEL_COOLDOWN_SECONDS = 2.0  # espera menor após cancelar manualmente

# ---------- CÂMERA: FRICÇÃO DE TROCA ----------
# Impede "pingue-pongar" entre câmeras instantaneamente todo frame.
CAMERA_SWITCH_COOLDOWN = 0.6

# ---------- ALARMES FALSOS ----------
# Eventos que parecem uma anomalia real (mesmo visual/som) mas custam pouca
# estabilidade de verdade — obrigam o jogador a checar a barra, não só reagir
# ao susto.
FALSE_ALARM_STABILITY_COST = 3

# ---------- BLECAUTE ----------
BLACKOUT_DURATION = 3.5

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
        "call_window_mult": 1.00,     # tempo pra responder um chamado
    },
}
DEFAULT_DIFFICULTY = {  # usado como fallback se alguma noite não estiver configurada acima
    "decay_mult": 1.5, "protocol_drain_mult": 1.4, "cam_switch_mult": 1.3, "call_window_mult": 0.75,
}

# ---------- CHAMADOS (mecânica nova) ----------
# Um paciente pode "chamar" o jogador: fica destacado bem visível no HUD
# (independente de qual câmera está ativa) e precisa ser respondido —
# câmera na sala certa + segurar/apertar a tecla de resposta — dentro de
# uma janela de tempo, ou a estabilidade dele leva um tapa. É o que
# obriga a alternar de câmera por decisão própria, em vez de escolher uma
# e esperar. Complementa (não substitui) o protocolo: chamado é reativo e
# rápido, protocolo é a ferramenta pesada pra estabilidade baixa.
CALL_RESPONSE_WINDOW = 11.0     # segundos para responder antes de falhar
CALL_STABILITY_GAIN = 14        # ganho de estabilidade ao responder a tempo
CALL_STABILITY_PENALTY = 18     # perda de estabilidade se o chamado expirar
CALL_COOLDOWN_SECONDS = 22.0    # espera mínima antes do mesmo paciente chamar de novo
CALL_AUTOCALL_CHANCE = 0.06     # chance/seg de chamado espontâneo (paciente MOVENDO ou pior)

# ---------- VISUAL / ATMOSFERA ----------
COLOR_BG_TOP = (8, 9, 13)
COLOR_BG_BOTTOM = (16, 18, 24)
COLOR_VIGNETTE = (0, 0, 0)
SCANLINE_ALPHA = 22          # opacidade das linhas de CRT nas câmeras
SCANLINE_SPACING = 3
CRT_GLOW_COLOR = (60, 200, 170)
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
