"""
nights.py
Define o roteiro de eventos de cada noite (tempo in-game -> evento).
Separado de event_manager.py para facilitar balanceamento/edição de conteúdo
sem mexer na lógica que executa os eventos.

Tempo é dado em "minutos in-game" dentro da janela 00:00-06:00,
convertido pelo EventManager para segundos reais da noite.

Tipos de evento disponíveis (ver event_manager.py para os handlers):
  light_flicker       — luz pisca (efeito visual só)
  patient_move        — paciente troca de sala
  camera_interference — estática numa câmera aleatória por alguns segundos
  anomaly_sighting     — avistamento REAL: efeito visual + acelera o
                          decaimento do paciente por um tempo (custa de verdade)
  false_alarm          — visual e som IDÊNTICOS ao anomaly_sighting, mas
                          quase não custa estabilidade — só a barra denuncia
  patient_disappear    — paciente some de todas as câmeras por um tempo
  blackout              — todas as câmeras apagam por alguns segundos
  patient_call          — paciente "chama": HUD destaca ele, e o jogador
                          precisa apontar a câmera certa + apertar [R]
                          dentro da janela de tempo (settings.CALL_*) ou
                          perde estabilidade. Também pode disparar sozinho
                          (ver patient.py, CALL_AUTOCALL_CHANCE) — usar
                          aqui garante que pelo menos um chamado roteirizado
                          sempre aconteça, mesmo com sorte no aleatório.
  jumpscare_event       — susto roteirizado (tela toda, independe da câmera)
  special_event         — evento cosmético/sonoro pontual
  final_event            — marca a reta final da noite
"""

# Cada evento é um dicionário:
# {
#   "time": minutos in-game (0-360) em que o evento dispara,
#   "type": tipo do evento (ver lista acima),
#   "payload": dados extras usados pelo handler (opcional),
# }

NIGHT_1_EVENTS = [
    {"time": 40, "type": "light_flicker", "payload": {}},
    {"time": 65, "type": "patient_call", "payload": {"patient_id": 1}},
    {"time": 85, "type": "patient_move", "payload": {"patient_id": 1}},
    {"time": 120, "type": "false_alarm", "payload": {"patient_id": 2}},
    {"time": 150, "type": "camera_interference", "payload": {}},
    {"time": 175, "type": "patient_call", "payload": {"patient_id": 2}},
    {"time": 195, "type": "patient_move", "payload": {"patient_id": 2}},
    {"time": 230, "type": "anomaly_sighting", "payload": {"patient_id": 2}},
    {"time": 260, "type": "blackout", "payload": {}},
    {"time": 285, "type": "patient_call", "payload": {"patient_id": 1}},
    {"time": 300, "type": "special_event", "payload": {"kind": "corridor_glimpse"}},
    {"time": 330, "type": "jumpscare_event", "payload": {}},
    {"time": 355, "type": "final_event", "payload": {}},
]

NIGHT_EVENTS = {
    1: NIGHT_1_EVENTS,
}
# Versão atual do jogo tem só a Noite 1 (protótipo em foco/polimento).
# Pra trazer a Noite 2/3 de volta: escrever NIGHT_2_EVENTS (mesmo formato
# acima), registrar aqui como `2: NIGHT_2_EVENTS`, dar um valor a
# settings.NIGHT_DIFFICULTY[2] e subir FINAL_NIGHT em game.py.

# Pequenos textos de "log" mostrados na UI quando um evento ocorre.
# Mantidos neutros e não estigmatizantes em relação a saúde mental.
# Importante: "false_alarm" usa DE PROPÓSITO o mesmo texto de
# "anomaly_sighting" — o log não pode denunciar qual é qual, senão perde a
# graça de precisar checar a barra de estabilidade.
EVENT_LOG_TEXT = {
    "light_flicker": "As luzes do corredor oscilaram por um instante.",
    "patient_move": "Um paciente se deslocou para outra sala.",
    "camera_interference": "Interferência momentânea em uma das câmeras.",
    "anomaly_sighting": "Registro incomum em uma das câmeras. Verifique.",
    "false_alarm": "Registro incomum em uma das câmeras. Verifique.",
    "patient_disappear": "Paciente fora do campo de visão de todas as câmeras.",
    "blackout": "Sinal de todas as câmeras foi perdido por um instante.",
    "patient_call": "Um paciente está pedindo atenção. Aponte a câmera certa.",
    "call_expired": "Ninguém respondeu ao chamado a tempo.",
    "jumpscare_event": "Algo se moveu bem perto de uma das câmeras.",
    "special_event": "Algo diferente aconteceu nesta noite.",
    "final_event": "O turno está prestes a terminar.",
}
