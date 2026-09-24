# Turno Noturno — Centro de Observação Clínica — v11.4

Protótipo jogável em Pygame, inspirado na estrutura de monitoramento por
câmeras (estilo FNAF), com escopo reduzido para 2 semanas de produção.
O jogador observa 2 pacientes por câmeras durante um turno noturno e
precisa manter a estabilidade de ambos, alternando protocolos preventivos
com pedidos de medicamentos. A câmera da farmácia, a bandeja e o primeiro
atendimento guiado já estão implementados. Esta revisão acrescenta a história
da Noite 1, registros opcionais, uma decisão no amanhecer e nova arte de susto.

Para apresentar o enredo aos professores, veja `HISTORIA_E_ROTEIRO.md`.
Para a origem da nova arte e como substituí-la, veja `ARTE_E_PROMPTS.md`.

A versão **11.4** permite jogar do menu ao desfecho **só com o mouse** ou
**só com o teclado**. O protocolo tem um botão de clicar e segurar, o botão
decorativo "Iniciar" foi removido e a pixelização agora é **fixa em 30%**.
Veja `CORRECOES_V11.4.md`, `VISUAL_PIXELADO.md` e as capturas em `previas`.

## Pedidos: como jogar

1. Por volta dos 20 segundos, o Paciente 02 faz o primeiro chamado. Vá à
   câmera indicada no painel e use `R` (ou clique em **Ouvir pedido**).
2. A lista aparece à direita. Clique na aba **Farmácia** ou use `F5`.
3. Retire os medicamentos clicando nas prateleiras ou usando os atalhos
   indicados. A bandeja comporta três itens. Nome, código, cor e símbolo
   identificam cada frasco; não é preciso distinguir só pela cor.
4. Volte à câmera do paciente e clique em **Entregar bandeja** ou use `R`. Se ele mudou de sala,
   localize-o nas câmeras. O painel guarda o último contato conhecido.
5. Continue observando e estabilizando ambos: a noite avança durante a coleta
   e durante os protocolos.

O primeiro pedido tem um item e 70 segundos, sem penalidade ao expirar; o
paciente permanece na sala durante esse atendimento. Nos seguintes, há de
1 a 3 itens diferentes, com pedidos menores mais frequentes. Só existe um
pedido por vez. Após entrega ou expiração, há 32–48 segundos de intervalo.
Pedidos normais de 1/2/3 itens duram 30/40/50 segundos e recuperam 14/20/26
pontos de estabilidade; expirar custa 18. O ganho é limitado a 100.

Itens errados podem ser removidos clicando na bandeja ou usando `BACKSPACE`
para o último. Uma entrega incompleta ou com extras é recusada sem penalidade
adicional. Não é possível acumular itens para pedidos futuros. O protocolo
não conclui nem apaga um pedido, e o prazo continua correndo durante ele.

Os seis medicamentos (Lume, Aster, Nimbo, Vesper, Orbe e Nexo) são fictícios.
Veja `MECANICA_PEDIDOS.md` para o mapa de parâmetros e pontos para playtest.

## História implementada

Hospital Nossa Senhora da Piedade, 1996. Marina Duarte chega para acompanhar
o plantão e avaliar o VIGIA, sistema de observação do hospital. Daniel
(Paciente 01) e Elias (Paciente 02) relatam batidas nos corredores. Os arquivos
automáticos insistem em registrar que nada aconteceu.

A abertura tem três páginas, com leitura antes de começar o relógio. Durante
os seis minutos de jogo, falas de Almeida, dos pacientes e de Marina ligam
os atendimentos, uma ficha antiga e o apagão ao mistério. As falas aparecem
como legendas de rádio; não há dublagem. Quando a tela do protocolo bloqueia
a leitura, a legenda aguarda, mas o mundo e os pedidos continuam contando.

Há três descobertas opcionais. Use `F` ou **Guardar registro** para salvar
a próxima descoberta pendente. Guardar não cura, não pausa o jogo e não tem
prazo próprio. Ao chegar às seis com os dois pacientes estáveis, releia seus
registros e escolha entre contestar o relatório com seu diário ou assinar a
versão automática. A escolha e a quantidade de registros guardados produzem
três variantes de epílogo. Os registros valem para aquele turno; recomeçar os limpa.

> **Estado atual:** só a Noite 1 está no jogo — Noite 2/3 foram tiradas
> de propósito pra focar o polimento numa única noite antes de expandir
> de novo (o código pra trazê-las de volta continua todo documentado,
> ver "Sobre a dificuldade por noite" mais abaixo).

## Visual: "PC velho" estilo Windows 95

Toda a interface fora do feed de câmera em si (menu, HUD, avisos,
protocolo) imita janelas 3D de sistema antigo: botões cinza com relevo,
barra de título azul e barra de tarefas. As cores ficam em `settings.py`.
O painel de atendimento permanece ao lado da câmera. A farmácia usa
prateleiras geométricas e frascos desenhados pela própria interface.

O feed de câmera mantém seu próprio visual de "gravação" (scanlines,
vinheta, ruído, ver `camera_system.py`) de propósito — é o conteúdo
sendo exibido dentro da janela, não o chrome do sistema.

Cenário e pacientes são pixelizados juntos antes dos textos e das bordas.
A imagem é reduzida para 30% da largura e da altura do feed antes de ampliar
sem interpolação. A estética é fixa nas câmeras e no jumpscare.
Os nomes, legendas, pedidos, frascos da interface e botões continuam legíveis.
Os arquivos de imagem originais permanecem intactos.

O botão "X" da janela principal volta ao menu. Dentro do protocolo, o "X"
cancela o procedimento e aplica a recarga de cancelamento, como ESC. Na tela
final, escolha um relatório para encerrar a história. O botão decorativo
"Iniciar" foi removido do rodapé. Ao lado do relógio, **Tela cheia / Janela**
permite alternar a exibição com o mouse.

## Como rodar

```bash
python -m venv .venv
# Windows:
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
# Linux/macOS: use .venv/bin/python nos dois comandos acima.
```

A única dependência do jogo é `pygame-ce`; não instale `pygame` e `pygame-ce`
no mesmo ambiente. O filtro usa `pygame.transform.grayscale()` e os sons são
WAVs já incluídos: não há dependência de NumPy. PyInstaller só serve para build.

No Windows, `jogar.bat` abre primeiro a build pronta, se ela existir, e
usa o Python instalado apenas como fallback. A janela se adapta à resolução
disponível sem cortar a interface; `F11` alterna tela cheia.

Controles (teclado e mouse funcionam em paralelo — use o que preferir):

- `←/→` ou `A/D`, **ou clique numa aba**: trocar de câmera
- `F1`–`F4`: ir direto para a câmera correspondente; `F5`: farmácia
- `1`/`2`, **ou clique em Estabilizar / na barra de estabilidade**: iniciar protocolo do Paciente 01/02
  (em qualquer estabilidade acima de zero, com paciente visível e sem recarga)
- **Clique e segure o botão do protocolo**, ou segure `ESPAÇO`: avançar até concluir
  (soltar, sair do botão ou perder o foco interrompe o gesto; a noite continua)
- `R`, **ou clique no botão do pedido**: ouvir o pedido / entregar a bandeja (paciente visível)
- `Q/W/E/Z/X/C`, **ou clique numa prateleira**: retirar um medicamento na farmácia
- `BACKSPACE`, **ou clique no item da bandeja**: remover um item escolhido
- `F`, **ou Guardar registro**: guardar a próxima descoberta pendente no diário
- `ESC`, **Cancelar ou X**: cancelar protocolo / voltar ao menu conforme a tela
- `ENTER`, **ou clique num botão**: confirmar em menus
- Na abertura: clique em **Mostrar texto completo / Continuar / Iniciar turno**
  ou use `ENTER`; **Voltar** ou `←` volta uma página
- No encerramento: setas selecionam, `ENTER` confirma; clique em **Reler** para ver um registro
- `F11`, **ou Tela cheia / Janela junto ao relógio**: alternar o modo de exibição
- **Sair**, **X do menu** ou `ESC` no menu: fechar o jogo

## Gerando a build da feira (Windows)

1. Extraia este ZIP numa pasta nova e execute `build_windows.bat` no Windows.
2. Aguarde a mensagem de conclusão.
3. Copie a pasta inteira `dist\TurnoNoturno` para o computador da feira.
4. Teste `TurnoNoturno.exe` nessa máquina antes do evento.

A build é feita dentro de `.build-venv`, sem alterar os pacotes globais do
computador, e instala apenas dependências com versões binárias prontas. O
projeto usa `pygame-ce`, compatível com o mesmo `import pygame` e com Python
3.14. A build inclui código, Pygame e assets, sem NumPy; o computador de exibição
não precisa ter Python instalado. O save fica ao lado do executável.

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
├── patient.py           # modelo de paciente (estabilidade, estado, sala)
├── medication.py        # pedidos, seis medicamentos e bandeja
├── care_ui.py           # painel de atendimento e farmácia
├── shift_log.py         # acontecimentos reais e relatório de derrota
├── story.py             # abertura, falas, descobertas e variantes de epílogo
├── story_ui.py          # páginas, legendas, diário e decisão final
├── event_manager.py     # dispara os eventos roteirizados/pseudoaleatórios
├── savegame.py           # persistência da noite mais alta desbloqueada
├── ui.py                # HUD, menus, telas de intro/fim de noite
├── audio.py              # reprodução de WAV/OGG incluídos, sem NumPy
├── tests/                # regressões de protocolo, render e áudio
├── tools/                # gerador opcional de WAVs (biblioteca padrão)
└── assets/
    ├── sprites/     -> substitua por sprites reais dos pacientes/cenário
    ├── backgrounds/ -> substitua por fundos reais de cada câmera
    ├── sounds/      -> efeitos WAV com os nomes esperados (ver audio.py)
    └── music/       -> música ambiente em loop
```

## Como o sistema funciona (visão geral)

- **Pacientes** (`patient.py`): cada um tem `stability` (0–100) que decai
  com o tempo — mais rápido se a câmera ativa não é a sala dele. O
  `state` (`NORMAL` → `INQUIETO` → `MOVENDO` → `ANORMAL` → `PERIGO`) é
  derivado automaticamente da estabilidade. Se a estabilidade chega a 0,
  a noite termina em derrota — precedida por um jumpscare.
- **Protocolo preventivo**: pode começar em qualquer estabilidade acima de
  zero, inclusive 100, enquanto o paciente está visível e fora da recarga.
  O aviso aos 55 é apenas uma sugestão; não bloqueia o botão. Ao iniciar
  (`1`/`2` ou **Estabilizar**), o jogador precisa segurar `ESPAÇO` ou manter
  o clique esquerdo no botão do protocolo; durante esse tempo a tela de
  câmeras fica bloqueada, mas **a noite não pausa**: relógio, outro paciente,
  chamados, eventos e blecautes continuam. A estabilidade do paciente em
  protocolo também continua caindo (`PROTOCOL_DRAIN_RATE` em `settings.py`).
  São 4 segundos de execução, perda de 1 ponto/s e recuperação de 50 ao concluir
  (limitada a 100). Use cedo para prevenir; usar com a barra quase cheia
  desperdiça recuperação. Se chegar a 0 antes do fim, ainda há derrota.
  A recarga de **25 segundos é individual**, começa na conclusão e não bloqueia
  o outro paciente. Cancelar não recupera pontos e aplica 6 segundos de recarga.
  Durante a tela de protocolo nenhum paciente recebe o bônus de observação.
  Pedidos continuam ativos durante o protocolo, inclusive do próprio paciente.
  Esses valores são uma base para playtest, não uma garantia de equilíbrio final.
- **Pedidos** (`medication.py`): substituem os antigos chamados de resposta
  instantânea. A agenda aleatória tem um único pedido por vez e intervalo
  garantido após sua resolução. O primeiro é guiado. Não começa um pedido
  cujo prazo ultrapassaria o fim da noite. Os pacientes não entram na farmácia.
- **Falas**: a faixa de rádio na base da câmera mostra comentários ao receber pedidos e
  entregar medicamentos, além de relatos sobre luzes e sombras ligados aos
  eventos reais do roteiro. O relato de sombra é o mesmo nos alarmes falsos
  e nas anomalias: ainda é preciso observar o paciente. Falas importantes
  entram numa fila; agradecimentos rotineiros não encobrem o roteiro.
- **História e diário** (`story.py`): o primeiro atendimento concluído revela
  um relato; visitar a farmácia após 90s, com sinal e livre para interagir,
  revela uma ficha; o apagão revela a omissão no relatório. Descobrir e guardar
  são ações separadas. Cada registro só pode ser guardado uma vez. O diário
  é opcional e afeta o epílogo, sem substituir os cuidados dos pacientes.
- **Derrota explicável** (`shift_log.py`): após o susto, mostra quem chegou
  a zero, a causa imediata, a situação da recarga do protocolo, o horário e
  os últimos três acontecimentos relevantes registrados. Distingue queda
  sem observação, crise, falha durante o protocolo e penalidade de pedido.
- **Câmeras** (`camera_system.py`): 5 câmeras fixas, com um pequeno
  cooldown ao trocar (`CAMERA_SWITCH_COOLDOWN`, também escalado pela
  dificuldade da noite) pra impedir alternar instantaneamente entre
  elas. Também suportam um evento de **blecaute** (`blackout`) em que
  nenhuma câmera mostra nada por alguns segundos — nesse período ninguém
  está "sendo observado" (nem itens podem ser coletados/entregues), então os
  dois pacientes decaem no ritmo rápido. O feed é convertido de verdade
  para tons de cinza ao carregar e reutiliza fundos/sprites escalados,
  scanlines e vinheta em cache. Isso preserva a estética de câmeras analógicas
  antigas ligadas ao sistema VIGIA.EXE sem refazer filtros enormes a 60 FPS.
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
  a nova arte em `assets/sprites/jumpscare.png` e treme a tela. A aparição
  pertence ao sinal de vídeo, sem transformar os pacientes em monstros.
  Quatro escalas são preparadas ao carregar a UI, evitando redimensionar
  a imagem em cada frame do susto. Se o arquivo faltar, aparece SINAL PERDIDO.
- **Eventos da noite** (`nights.py` + `event_manager.py`): uma lista de
  eventos com o "minuto in-game" em que disparam. É só uma máquina de
  estados com timers — sem IA complexa. Adicionar/editar eventos é só
  mexer na lista `NIGHT_1_EVENTS`; todos os tipos disponíveis estão
  documentados no topo de `nights.py`.
- **Dificuldade por noite** (`settings.py` → `NIGHT_DIFFICULTY`): cada
  noite tem multiplicadores próprios (`decay_mult`, `protocol_drain_mult`,
  `cam_switch_mult`) que são passados pra `Patient` e
  `CameraSystem` quando a noite começa (`game.py::start_night`) — é o
  mecanismo que permite a Noite 2 ser mais dura que a Noite 1 quando ela
  voltar, sem duplicar lógica de balanceamento em cada lugar.
- **Áudio** (`audio.py`): carrega os 17 sons de `assets/sounds` e `assets/music`,
  incluindo as três batidas associadas ao mistério.
  Os sons de teste agora são WAVs pré-gerados, preservando os arquivos de áudio
  originais. Substitua-os mantendo os nomes de `SOUND_NAMES` para trocar a arte.
  Arquivo ausente/inválido gera aviso, sem derrubar o jogo. Sem dispositivo de
  áudio o jogo roda silenciosamente. Não há síntese nem NumPy em runtime.

## Ajustando a dificuldade

Todos os números de balanceamento ficam em `settings.py`, comentados:

| Constante | O que controla |
|---|---|
| `PROTOCOL_DRAIN_RATE` | quão rápido a estabilidade cai *durante* o protocolo |
| `PROTOCOL_COOLDOWN_SECONDS` | espera após um protocolo bem-sucedido |
| `PROTOCOL_CANCEL_COOLDOWN_SECONDS` | espera ao cancelar, sem recuperação |
| `PROTOCOL_RECOMMEND_THRESHOLD` | sugestão de uso na HUD; não restringe acionamento |
| `CAMERA_SWITCH_COOLDOWN` | espera entre trocas de câmera |
| `FALSE_ALARM_STABILITY_COST` | custo real de um alarme falso |
| `BLACKOUT_DURATION` | duração do blecaute |
| `DECAY_OBSERVED` / `DECAY_UNOBSERVED` | velocidade geral de deterioração |
| `NIGHT_DIFFICULTY[n]` | multiplicadores acima aplicados por noite (ver seção anterior) |
| `REQUEST_FIRST_AT` / `REQUEST_TUTORIAL_SECONDS` | início e prazo do primeiro pedido |
| `REQUEST_SECONDS` / `REQUEST_SIZE_WEIGHTS` | prazo e frequência de cada tamanho de pedido |
| `REQUEST_STABILITY_GAIN` / `REQUEST_EXPIRY_PENALTY` | recuperação da entrega / penalidade normal |
| `REQUEST_INTERVAL_MIN` / `REQUEST_INTERVAL_MAX` | descanso entre pedidos |
| `ROOM_CHANGE_CHANCE` / `ROOM_CHANGE_COOLDOWN` | chance por segundo e tempo mínimo entre movimentos |




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
| `pharmacy.png` (opcional) | CAM 05 — Ala Farmacêutica; sem arquivo usa prateleiras geométricas |

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

### Fonte (deixar a interface com identidade)
- **Fonte**: baixe uma fonte gratuita (ex: [Google Fonts](https://fonts.google.com) —
  algo condizente com o visual "PC antigo", tipo uma bitmap/pixelada ou a
  clássica MS Sans Serif) em formato `.ttf` e salve como
  `assets/fonts/main.ttf`. Ela passa a ser usada em **todo** o jogo (menu,
  HUD, telas) automaticamente — é a mudança que mais muda a cara da
  interface pelo menor esforço.
- **Jumpscare**: a imagem já incluída fica em `assets/sprites/jumpscare.png`.
  Para substituí-la, prefira PNG horizontal 16:9 com fundo opaco e rosto
  centralizado. O jogo preenche a tela, faz crop central e aplica tremor.
  O prompt da primeira arte está em `ARTE_E_PROMPTS.md`.

### Sons

Coloque arquivos `.wav` em `assets/sounds/` com os nomes listados em
`audio.py` (`blip.wav`, `alert.wav`, `static_burst.wav`, etc.). A música fica
em `assets/music/ambient_music.wav` (também aceita `.ogg`).

Para recriar somente sons de teste que estejam faltando, use
`python tools/generate_placeholder_audio.py`. Ele usa `math`, `array`, `random`
e `wave` da biblioteca padrão, não exige NumPy e não sobrescreve arquivos.

### Testes

`python -m unittest discover -s tests -v` executa regressões em modo sem janela.
Use o Python do ambiente virtual que contém Pygame. A build deve ser gerada
e testada no Windows para confirmar o `.exe`; testes Linux não substituem isso.

Os 40 testes incluem pedidos de 1–3 itens, erros de seleção, limites da bandeja,
teclado/mouse, localização, blecaute, protocolo, perda explicada, leitura da
abertura, registros, escolhas finais e uso da arte do jumpscare em cache.
Uma simulação completa o turno, entrega medicamentos, guarda os três registros
e escolhe um desfecho. Ela conhece as salas dos pacientes e verifica integração;
não substitui playtest humano de dificuldade e tempo de leitura.

## Fora do escopo (intencionalmente não implementado)

Combate, física complexa, multiplayer, IA avançada, mais de 2 pacientes,
inventário persistente, sistema de upgrades, mapa grande e cutscenes complexas.
A narrativa usa telas e legendas no sistema existente; ainda não há dublagem
nem cenas animadas. Só a Noite 1 está disponível.

## Notas sobre o tratamento do tema

Os dois pacientes (ansiedade e alterações de percepção) foram
desenhados como fonte de tensão e cuidado, não de ridicularização: o
jogo não usa os estados como "piada" nem atribui aos pacientes
comportamento violento ou perigoso para o jogador — o risco é sempre a
deterioração da própria estabilidade deles, e o objetivo do jogador é
ajudar, não se defender deles.

## Versão dos pacotes

A versão atual está no arquivo `VERSION`. A cada nova atualização entregue,
aumente a versão e mantenha o nome do ZIP, a pasta interna e este README
coerentes. Esta entrega usa `turno-noturno-v11.4.zip` e a pasta
`turno-noturno-v11.4`. Documentos de correções antigas mantêm sua versão histórica.
