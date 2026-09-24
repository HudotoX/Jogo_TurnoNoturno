"""História da Noite 1: roteiro, fila de falas, registros e desfechos.

Estado puro: o diário não altera estabilidade, relógio, pedidos ou protocolos.
"""
from collections import deque
from dataclasses import dataclass

HOSPITAL_NAME = "Hospital Nossa Senhora da Piedade"
PROTAGONIST = "Marina Duarte"
PATIENT_NAMES = {1: "Daniel", 2: "Elias"}

INTRO_PAGES = (
    {
        "title": "23h48 · A chegada",
        "text": (
            "Hospital Nossa Senhora da Piedade, 1996.\n\n"
            "Você é Marina Duarte, pesquisadora recém-chegada. Foi chamada para acompanhar "
            "o plantão e avaliar os registros do VIGIA, o sistema de observação do hospital.\n\n"
            "Daniel e Elias passaram as últimas noites relatando batidas no corredor. "
            "Os relatórios, sempre idênticos, dizem que nada aconteceu.\n\n"
            "Sua tarefa nesta noite é cuidar dos dois até as seis e descobrir por que "
            "os registros não combinam com o que eles contam."
        ),
    },
    {
        "title": "23h56 · A passagem de plantão",
        "text": (
            "Almeida, o coordenador, deixa o rádio ligado:\n\n"
            "“Daniel é o Paciente 01. Elias, o 02. Observe as câmeras, atenda os pedidos "
            "e use o protocolo antes que a estabilidade acabe. Só olhar não basta.”\n\n"
            "Ele aponta para a impressora:\n\n"
            "“O VIGIA prepara o relatório ao amanhecer. A direção espera a sua assinatura.”\n\n"
            "Entre as folhas, você encontra um bilhete: “Escute primeiro. Confira depois. "
            "Não deixe o sistema escrever a noite por você.”"
        ),
    },
    {
        "title": "00h00 · O seu registro",
        "text": (
            "Você separa um disquete para guardar suas anotações. O primeiro chamado "
            "deve chegar em instantes.\n\n"
            "Clique nas abas para trocar de câmera (F1–F5).\n"
            "Clique em Estabilizar (1/2) e segure o botão ou ESPAÇO.\n"
            "Ouça e entregue pedidos pelo botão do painel (R).\n"
            "Na farmácia, clique nos medicamentos solicitados.\n\n"
            "Quando encontrar algo relevante, use F ou clique em Guardar registro. "
            "Investigar é opcional; manter os dois pacientes estáveis vem primeiro.\n\n"
            "Às seis, você decidirá o que vai constar no relatório."
        ),
    },
)

CLUES = {
    "relato": {
        "title": "O relato ouvido",
        "source": "Atendimento de um paciente",
        "text": "Após uma entrega, um paciente descreveu batidas no corredor durante as falhas de luz. "
                "O relato foi registrado com suas próprias palavras, sem virar automaticamente um erro de percepção.",
    },
    "ficha": {
        "title": "A ficha de 1991",
        "source": "Arquivo da farmácia",
        "text": "Uma ficha antiga contém a mesma descrição de batidas. O texto foi riscado e substituído "
                "por 'SEM OCORRÊNCIAS'. A alteração tem data de cinco anos antes deste plantão.",
    },
    "falha": {
        "title": "O apagão omitido",
        "source": "Sinal das câmeras / registro automático",
        "text": "As cinco câmeras perderam o sinal durante o turno. Mesmo assim, a prévia automática "
                "do VIGIA marcou 'SEM OCORRÊNCIAS'. A falha foi observada no sistema, além dos relatos dos pacientes.",
    },
}

# Tempos em segundos reais dentro da noite de seis minutos.
STORY_BEATS = (
    (5, "ALMEIDA · RÁDIO", "Marina, o rádio está aberto. Daniel é o Paciente 01; Elias, o 02. "
     "Se algo não bater com o relatório, guarde a sua anotação."),
    (76, "ALMEIDA · RÁDIO", "Há fichas antigas na farmácia. A direção pediu que eu descartasse tudo. "
     "Deixei uma cópia no balcão. Talvez explique esses relatos."),
    (165, "VIGIA · PRÉVIA DO RELATÓRIO", "00h00–02h45: SEM OCORRÊNCIAS. "
     "Relatos sem confirmação serão classificados como falhas de percepção."),
    (215, "MARINA · ANOTAÇÃO PESSOAL", "Daniel e Elias precisam de atendimento, mas isso não torna "
     "cada palavra deles um erro. Vou conferir o que o VIGIA está deixando de fora."),
    (292, "ALMEIDA · RÁDIO", "Reconheço essa frase do relatório. Ela já estava nos plantões de 1991. "
     "Não sei o que aparece nas câmeras. Sei que apagaram o que alguém tentou contar."),
    (338, "MARINA · ANOTAÇÃO PESSOAL", "Os dois pacientes continuam nas alas. Aquela imagem apareceu "
     "dentro do sinal. Preciso terminar o atendimento e preservar o que conseguir."),
    (351, "ALMEIDA · RÁDIO", "A equipe da manhã está chegando. O VIGIA vai pedir sua assinatura. "
     "Leia o relatório antes de confirmar, Marina."),
)


@dataclass
class StoryMessage:
    speaker: str
    text: str
    duration: float
    important: bool = True


class Story:
    def __init__(self):
        self.queue = deque()
        self.current = None
        self.message_left = 0.0
        self.last_message = None
        self.next_beat = 0
        self.discovered = []
        self.recorded = []
        self.choice = None
        self.ending_selected = 0
        self.review_key = None
        self._seen_messages = set()

    def say(self, speaker, text, key=None, important=True):
        if key is not None:
            if key in self._seen_messages:
                return
            self._seen_messages.add(key)
        # Falas rotineiras de agradecimento não encobrem nem acumulam sobre o roteiro.
        if not important and (self.current is not None or self.queue):
            return
        duration = max(8.0, min(15.0, len(text) / 14.0 + 2))
        self.queue.append(StoryMessage(speaker, text, duration, important))

    def update(self, dt, elapsed, can_read=True):
        while self.next_beat < len(STORY_BEATS) and elapsed >= STORY_BEATS[self.next_beat][0]:
            _, speaker, text = STORY_BEATS[self.next_beat]
            self.say(speaker, text, key=f"beat-{self.next_beat}")
            self.next_beat += 1
        if not can_read:
            return  # só a exposição da legenda aguarda; o jogo segue normalmente
        if self.current is not None:
            self.message_left = max(0.0, self.message_left - dt)
            if self.message_left <= 0:
                self.last_message = self.current
                self.current = None
        if self.current is None and self.queue:
            self.current = self.queue.popleft()
            self.message_left = self.current.duration

    def discover(self, key, speaker, text):
        if key not in CLUES or key in self.discovered:
            return False
        self.discovered.append(key)
        self.say(speaker, text, key=f"clue-{key}")
        return True

    def on_delivery(self, patient_id):
        name = PATIENT_NAMES.get(patient_id, f"Paciente {patient_id:02d}")
        return self.discover(
            "relato", f"{name.upper()} · PACIENTE {patient_id:02d}",
            "Obrigado por voltar. As batidas vêm do corredor quando a luz falha. "
            "No dia seguinte, dizem que eu imaginei. Anote o que eu falei, por favor.")

    def observe(self, elapsed, camera, blackout, can_interact):
        if elapsed >= 90 and camera == "CAM 05" and not blackout and can_interact:
            self.discover(
                "ficha", "MARINA · ARQUIVO DA FARMÁCIA",
                "Ficha de 1991: 'Batidas no corredor durante a falha de luz'. "
                "Alguém riscou o relato e escreveu 'SEM OCORRÊNCIAS' por cima.")

    def on_blackout(self):
        self.discover(
            "falha", "MARINA · REGISTRO DO SINAL",
            "Todas as câmeras apagaram. A prévia do VIGIA acabou de registrar 'SEM OCORRÊNCIAS'. "
            "Desta vez eu vi a falha acontecer. Vou guardar isso.")

    @property
    def pending_clue(self):
        return next((key for key in self.discovered if key not in self.recorded), None)

    def record_next(self):
        key = self.pending_clue
        if key is None:
            return None
        self.recorded.append(key)
        return key

    def choose(self, choice):
        if choice not in ("preserve", "automatic") or self.choice is not None:
            return False
        self.choice = choice
        return True

    def ending(self):
        count = len(self.recorded)
        if self.choice == "automatic":
            return "SEM OCORRÊNCIAS", (
                "Às seis, Daniel e Elias são recebidos pela equipe da manhã. Você assina a versão automática do plantão.",
                "O arquivo oficial encerra a noite com a mesma frase de sempre: 'SEM OCORRÊNCIAS'. "
                "Os relatos dos pacientes e suas dúvidas ficam fora do documento.",
                "Ao sair, você escuta três batidas atrás da sala de monitoramento. "
                "Na impressora, o próximo relatório já começou a ser escrito.",
            )
        if count >= 2:
            return "UMA NOITE REGISTRADA", (
                "Às seis, Daniel e Elias são recebidos pela equipe da manhã. "
                "Você anexa suas anotações ao relatório e guarda uma cópia no disquete.",
                f"{count} registros acompanham sua assinatura. Almeida aceita assinar como testemunha "
                "do plantão. As versões anteriores serão comparadas com o que vocês preservaram.",
                "Você ainda não sabe o que apareceu no sinal. Mas esta noite deixou um rastro que o VIGIA "
                "não conseguiu resumir a 'SEM OCORRÊNCIAS'. Ao desligar o monitor, a imagem demora um segundo a desaparecer.",
            )
        return "O PRIMEIRO TESTEMUNHO", (
            "Às seis, Daniel e Elias são recebidos pela equipe da manhã. "
            "Você se recusa a confirmar que nada aconteceu.",
            ("Seu único registro acompanha uma declaração pessoal. " if count == 1 else
             "Sem registros guardados, você escreve uma declaração pessoal. ") +
            "Há lacunas que você não consegue preencher. Almeida guarda a declaração, mas pede "
            "mais documentação antes de contestar os arquivos antigos.",
            "O mistério permanece. Pela primeira vez, porém, alguém encerra o turno "
            "sem transformar todas as perguntas dos pacientes em erro.",
        )
