# Turno Noturno v11.4

## Controle completo por mouse

| Ação | Mouse | Teclado |
| --- | --- | --- |
| Começar / sair | Botões do menu | Setas e Enter; Esc sai do menu |
| Ler a abertura | Mostrar texto completo, Continuar e Voltar | Enter e seta esquerda |
| Trocar de câmera | Abas superiores | F1–F5 ou setas/A/D |
| Iniciar protocolo | Estabilizar abaixo da barra do paciente | 1/2 |
| Executar protocolo | Clicar e segurar o botão na janela | Segurar Espaço |
| Cancelar protocolo | Cancelar ou X da janela | Esc |
| Ouvir / entregar pedido | Botão no painel de atendimento | R |
| Retirar medicamento | Clicar no frasco/prateleira | Q/W/E/Z/X/C |
| Retirar item da bandeja | Clicar no item | Backspace remove o último |
| Guardar registro | Botão na legenda | F |
| Escolher o relatório | Botões da tela final | Setas e Enter |
| Voltar ao menu | X durante o turno ou botão na tela final | Esc/Enter, conforme a tela |
| Tela cheia / janela | Botão próximo ao relógio | F11 |

Os cliques usam as mesmas áreas dos botões desenhados e são convertidos para
as coordenadas do jogo quando a janela está reduzida ou com barras pretas.
Os atalhos do teclado continuam funcionando, inclusive junto do mouse.

O protocolo só avança enquanto houver um clique segurado no botão ou Espaço
pressionado. Usar os dois juntos não acelera a ação. Soltar, sair do botão,
sair da janela, perder o foco ou redimensionar libera o gesto do mouse.
Cancelamentos, transições, conclusões e sustos também limpam esse estado.
Depois de uma interrupção, é preciso apertar o botão novamente.

Soltar o botão não cancela o protocolo: o progresso fica onde estava,
mas a estabilidade e os prazos continuam correndo, como no controle por teclado.
Cancelar aplica a recarga já existente de 6 segundos. Concluir aplica a
recuperação e a recarga normal de 25 segundos.

## Interface e visual

- Botão decorativo "Iniciar" retirado do canto inferior esquerdo.
- Botões Estabilizar adicionados às barras dos pacientes, com indicação de
  indisponibilidade quando é preciso localizar o paciente ou esperar a recarga.
- Janela do protocolo ampliada, com botão de segurar e cancelamento explícito.
- Instruções da abertura e do atendimento explicam o uso por mouse.
- X do menu agora fecha o jogo. Na derrota, Voltar ao menu e X funcionam;
  clicar fora dos botões não dispensa o relatório sem querer.
- Tela cheia / Janela disponível por clique junto ao relógio.
- Pixelização fixa em 30% nas câmeras e no susto. Seletor, indicação F6 e
  persistência de preferências visuais retirados.

## Verificação

48 testes automatizados passaram, incluindo os 40 anteriores. O novo teste
de integração percorre o menu, a abertura, uma noite inteira, protocolos,
entregas, os três registros, a escolha final e a saída usando apenas eventos
de mouse. Os cliques passam pela conversão de uma janela 1280×800 com barras
pretas. O teste de noite completa por teclado continua passando.

O piloto de teste conhece a posição dos pacientes: ele verifica o funcionamento
do fluxo, não mede a dificuldade para um jogador humano. Foram conferidas
capturas da interface em 1920×1080 e 1280×720, além das interrupções do gesto
de segurar o mouse e do uso simultâneo com o teclado.

## Abrir e atualizar

Extraia `turno-noturno-v11.4.zip` em uma pasta nova e use `jogar.bat`.
Se você utiliza o executável, rode `build_windows.bat` no Windows para gerar
uma build com o código desta versão. O ZIP contém o projeto e os assets;
não inclui um novo executável Windows. Validação realizada em Linux com
pygame-ce 2.5.8; a build Windows deve ser gerada e aberta no Windows.
