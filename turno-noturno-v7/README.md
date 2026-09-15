# Turno Noturno — Centro de Observação Clínica

Protótipo jogável em Pygame, inspirado na estrutura de monitoramento por
câmeras (estilo FNAF), com escopo reduzido para 2 semanas de produção.
O jogador observa 2 pacientes por câmeras durante um turno noturno e
precisa manter a estabilidade psicológica de ambos, aplicando um
"protocolo de estabilização" quando necessário — sem poder monitorar
as câmeras enquanto o faz.

> **Estado atual:** só a Noite 1 está no jogo — Noite 2/3 foram tiradas
> de propósito pra focar o polimento numa única noite antes de expandir
> de novo (o código pra trazê-las de volta continua todo documentado,
> ver "Sobre a dificuldade por noite" mais abaixo).

## Como rodar

```bash
pip install -r requirements.txt
python main.py
```

Controles:

- `←/→` ou `A/D`: trocar de câmera
- `1`–`4`: ir direto para a câmera correspondente
- `1`/`2` (com o HUD pedindo): iniciar protocolo do Paciente 01/02
- `ESPAÇO` (segurar): concluir o protocolo em andamento
- `R`: responder a um chamado (precisa estar com a câmera certa na tela)
- `ESC`: cancelar protocolo / voltar ao menu
- `ENTER`: confirmar em menus

## Progresso salvo

Versão atual do jogo tem só a Noite 1 (protótipo em foco/polimento —
ver "Sobre a Noite 2/3" mais abaixo). O jogo ainda guarda a noite mais
alta já vencida (arquivo `save_turno_noturno.json`, ao lado do jogo),
então quando as próximas noites voltarem, perder uma delas não vai
mandar ninguém de volta pra Noite 1 — o menu oferece "Continuar —
Noite X" e, separadamente, "Recomeçar do zero". Um save corrompido ou
ausente nunca impede o jogo de abrir.

## Transições de cena

Toda troca de tela (menu → intro da noite → jogo → fim de noite → menu
de novo) passa por um fade-to-black rápido em vez de cortar seco —
`game.py::_go_to()` centraliza isso: escurece, troca de estado
exatamente no instante em que a tela está preta, clareia de volta. A
duração de cada metade é `settings.SCENE_TRANSITION_SECONDS`. O
jumpscare continua sendo um corte seco de propósito (a transição
suave ali diluiria o susto).

## Estrutura do projeto

```
game/
├── main.py            # ponto de entrada, loop principal
├── settings.py         # todas as constantes de balanceamento
├── nights.py            # roteiro de eventos de cada noite (dados, não lógica)
├── game.py              # máquina de estados e orquestração
├── camera_system.py     # troca de câmeras e desenho do feed placeholder
├── patient.py           # modelo de paciente (estabilidade, estado, sala, chamados)
├── event_manager.py     # dispara os eventos roteirizados/pseudoaleatórios
├── savegame.py           # persistência da noite mais alta desbloqueada
├── ui.py                # HUD, menus, telas de intro/fim de noite
├── audio.py              # efeitos sonoros (sintetizados, com fallback p/ arquivos reais)
└── assets/
    ├── sprites/     -> substitua por sprites reais dos pacientes/cenário
    ├── backgrounds/ -> substitua por fundos reais de cada câmera
    ├── sounds/      -> coloque .wav com os nomes esperados (ver audio.py) para
    │                   sobrescrever os sons sintetizados automaticamente
    └── music/       -> música ambiente (ainda não conectada ao loop; ver notas)
```

## Como o sistema funciona (visão geral)

- **Pacientes** (`patient.py`): cada um tem `stability` (0–100) que decai
  com o tempo — mais rápido se a câmera ativa não é a sala dele. O
  `state` (`NORMAL` → `INQUIETO` → `MOVENDO` → `ANORMAL` → `PERIGO`) é
  derivado automaticamente da estabilidade. Se a estabilidade chega a 0,
  a noite termina em derrota — precedida por um jumpscare.
- **Protocolo (com risco real)**: quando a estabilidade cai a 25 ou
  menos, o HUD sinaliza que o protocolo está disponível. Ao iniciar
  (`1`/`2`), o jogador precisa segurar `ESPAÇO`; durante esse tempo as
  câmeras ficam "congeladas" E a estabilidade do paciente **continua
  caindo** (`PROTOCOL_DRAIN_RATE` em `settings.py`, ajustado pela
  dificuldade da noite). Se ela chegar a 0 antes do progresso completar,
  é uma falha — jumpscare na hora. Cada paciente também tem um cooldown
  depois de um protocolo bem-sucedido (`PROTOCOL_COOLDOWN_SECONDS`) e um
  cooldown menor se for cancelado manualmente, pra impedir ficar
  "spammando" proteção nos dois pacientes.
- **Chamados (mecânica ativa, não reativa)**: um paciente pode "chamar" —
  seja porque um evento roteirizado disparou isso (`patient_call` em
  `nights.py`), seja sozinho, com uma chance pequena por segundo quando
  está mal (`CALL_AUTOCALL_CHANCE`). Aparece um banner vermelho no topo
  da tela, visível **independente de qual câmera está ativa**, com um
  cronômetro. O jogador precisa trocar pra câmera da sala certa e
  apertar `R` dentro da janela de tempo (`CALL_RESPONSE_WINDOW`, também
  ajustada pela dificuldade), ou o paciente perde estabilidade de
  verdade. É a peça que tira o jogo do "esperamento simulator": em vez
  de escolher uma câmera e ficar parado nela, o jogador precisa
  circular de propósito, senão perde chamados. Complementa o protocolo
  em vez de substituí-lo — chamado é rápido e reativo, protocolo é a
  ferramenta pesada pra estabilidade já crítica.
- **Câmeras** (`camera_system.py`): 4 câmeras fixas, com um pequeno
  cooldown ao trocar (`CAMERA_SWITCH_COOLDOWN`, também escalado pela
  dificuldade da noite) pra impedir alternar instantaneamente entre
  elas. Também suportam um evento de **blecaute** (`blackout`) em que
  nenhuma câmera mostra nada por alguns segundos — nesse período ninguém
  está "sendo observado" (nem chamados podem ser respondidos), então os
  dois pacientes decaem no ritmo rápido.
- **Anomalias reais vs. alarmes falsos**: o Paciente 02 (Percepção) pode
  disparar um `anomaly_sighting` (real — acelera o decaimento por um
  tempo) ou um `false_alarm` (visual e som **idênticos**, mas quase sem
  custo de estabilidade). O log de eventos usa o mesmo texto pros dois
  de propósito — só olhando a barra de estabilidade dá pra saber qual é
  qual.
- **Jumpscare** (`ui.py` / `game.py`): dispara sempre que o jogador
  falha em estabilizar alguém (protocolo zerado ou negligência total),
  além de poder ser roteirizado via evento `jumpscare_event` em
  `nights.py`. Congela o jogo por `JUMPSCARE_DURATION` segundos, mostra
  um rosto (procedural, ou `assets/sprites/jumpscare.png` se existir) e
  treme a tela.
- **Eventos da noite** (`nights.py` + `event_manager.py`): uma lista de
  eventos com o "minuto in-game" em que disparam. É só uma máquina de
  estados com timers — sem IA complexa. Adicionar/editar eventos é só
  mexer na lista `NIGHT_1_EVENTS`; todos os tipos disponíveis estão
  documentados no topo de `nights.py`.
- **Dificuldade por noite** (`settings.py` → `NIGHT_DIFFICULTY`): cada
  noite tem multiplicadores próprios (`decay_mult`, `protocol_drain_mult`,
  `cam_switch_mult`, `call_window_mult`) que são passados pra `Patient` e
  `CameraSystem` quando a noite começa (`game.py::start_night`) — é o
  mecanismo que permite a Noite 2 ser mais dura que a Noite 1 quando ela
  voltar, sem duplicar lógica de balanceamento em cada lugar.
- **Áudio** (`audio.py`): tenta carregar arquivos `.wav` reais de
  `assets/sounds/<nome>.wav`; se não existirem, sintetiza tons simples
  via `numpy` para não deixar o protótipo mudo. Basta soltar os
  arquivos finais com os nomes certos (ver o dicionário `specs` em
  `audio.py`) para substituir os placeholders sem tocar em nenhuma
  outra parte do código.

## Ajustando a dificuldade

Todos os números de balanceamento ficam em `settings.py`, comentados:

| Constante | O que controla |
|---|---|
| `PROTOCOL_DRAIN_RATE` | quão rápido a estabilidade cai *durante* o protocolo |
| `PROTOCOL_COOLDOWN_SECONDS` | espera após um protocolo bem-sucedido |
| `CAMERA_SWITCH_COOLDOWN` | espera entre trocas de câmera |
| `FALSE_ALARM_STABILITY_COST` | custo real de um alarme falso |
| `BLACKOUT_DURATION` | duração do blecaute |
| `DECAY_OBSERVED` / `DECAY_UNOBSERVED` | velocidade geral de deterioração |
| `NIGHT_DIFFICULTY[n]` | multiplicadores acima aplicados por noite (ver seção anterior) |
| `CALL_RESPONSE_WINDOW` | tempo pra responder um chamado |
| `CALL_STABILITY_GAIN` / `CALL_STABILITY_PENALTY` | ganho ao responder / custo ao deixar expirar |
| `CALL_COOLDOWN_SECONDS` | espera mínima antes do mesmo paciente chamar de novo |
| `CALL_AUTOCALL_CHANCE` | chance/seg de chamado espontâneo (fora dos roteirizados) |




## Substituindo os placeholders por arte final (o time faz os sprites)

O código já procura arquivos reais automaticamente — **não precisa mexer em
nenhuma linha de Python**, só desenhar e salvar com os nomes certos:

**Cenários** — um PNG por câmera, ~960×430 px, salvos em `assets/backgrounds/`:

| Arquivo | Câmera |
|---|---|
| `bed.png` | CAM 01 — Ala de Descanso |
| `hall.png` | CAM 02 — Corredor Central |
| `desk.png` | CAM 03 — Sala de Observação |
| `yard.png` | CAM 04 — Pátio Interno |

**Pacientes** — um PNG por paciente, ~140×200 px, **fundo transparente**,
salvos em `assets/sprites/`:

| Arquivo | Paciente |
|---|---|
| `patient_01.png` | Paciente 01 — Ansiedade |
| `patient_02.png` | Paciente 02 — Percepção |

O sprite é ancorado pelos pés (posicionado de baixo pra cima) e recebe
automaticamente um leve tingimento na cor do estado atual (amarelo, laranja,
roxo, vermelho) quando o paciente não está `NORMAL` — não é preciso desenhar
uma versão do sprite pra cada estado.

Assim que os arquivos existirem nessas pastas com esses nomes, rode o jogo
normalmente (`python main.py`) que a arte nova já aparece no lugar do
placeholder geométrico. Se algum arquivo não existir ainda, aquela peça
específica continua no placeholder — dá pra ir substituindo aos poucos.

### Fonte e fundo do menu (deixar a interface com identidade)
- **Fonte**: baixe uma fonte gratuita (ex: [Google Fonts](https://fonts.google.com) —
  algo condizente com o clima clínico/tenso, tipo uma mono ou uma serifada
  desgastada) em formato `.ttf` e salve como `assets/fonts/main.ttf`. Ela
  passa a ser usada em **todo** o jogo (menu, HUD, telas) automaticamente —
  é a mudança que mais muda a cara da interface pelo menor esforço.
- **Fundo do menu**: uma imagem 1000×650 (ou o tamanho que definirem em
  `settings.py`) salva como `assets/backgrounds/menu.png` substitui o
  fundo gerado por código nas telas de menu/intro/fim de noite.
- **Jumpscare**: uma imagem salva como `assets/sprites/jumpscare.png`
  (fundo transparente, algo dramático/close-up) substitui o rosto
  desenhado por código durante o susto.

### Sons

Coloque arquivos `.wav` em `assets/sounds/` com os nomes listados em
`audio.py` (`blip.wav`, `alert.wav`, `static_burst.wav`, etc.). Eles
substituem automaticamente os sons sintetizados, do mesmo jeito.

## Fora do escopo (intencionalmente não implementado)

Inventário, combate, física complexa, multiplayer, IA avançada, mais de
2 pacientes, mais de 4 câmeras, mais de 3 noites, sistema de upgrades,
mapa grande, cutscenes complexas — conforme definido no escopo do
projeto.

## Notas sobre o tratamento do tema

Os dois pacientes (ansiedade e alterações de percepção) foram
desenhados como fonte de tensão e cuidado, não de ridicularização: o
jogo não usa os estados como "piada" nem atribui aos pacientes
comportamento violento ou perigoso para o jogador — o risco é sempre a
deterioração da própria estabilidade deles, e o objetivo do jogador é
ajudar, não se defender deles.
