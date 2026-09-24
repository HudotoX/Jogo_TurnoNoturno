# Turno Noturno — história da Noite 1

Primeira versão implementada. Este documento contém spoilers e serve como
referência para a equipe e para a apresentação aos professores.

## Premissa

Hospital Nossa Senhora da Piedade, 1996. A pesquisadora Marina Duarte chega
para acompanhar um turno e avaliar o VIGIA, sistema que reúne as câmeras e
prepara o relatório do hospital. Os pacientes Daniel e Elias contam que ouvem
batidas no corredor durante falhas de luz. Os arquivos registram, noite após
noite, a mesma conclusão: SEM OCORRÊNCIAS.

Marina precisa cuidar dos dois até as seis. Ao longo do trabalho, encontra
indícios de que o sistema está omitindo acontecimentos. No amanhecer, terá
de decidir se assina o relatório automático ou contesta o documento com
aquilo que conseguiu preservar.

## Personagens

| Personagem | Papel no turno |
|---|---|
| Marina Duarte | Protagonista controlada pelo jogador; pesquisadora recém-chegada |
| Daniel / Paciente 01 | Relata as batidas e precisa de acompanhamento de estabilidade |
| Elias / Paciente 02 | Faz o primeiro pedido guiado; relata sombras e alterações no ambiente |
| Almeida | Coordenador que orienta pelo rádio e deixou uma ficha antiga na farmácia |
| Aparição no sinal | Presença sem identidade revelada; a nova arte do jumpscare |

Os pacientes continuam sendo pessoas que precisam de cuidado. A aparição
pertence ao sinal de vídeo. O conflito envolve o que o hospital registra e
o que escolhe desconsiderar; a origem da presença permanece aberta.

## Começo, desenvolvimento e conclusão

**Começo:** três páginas apresentam a chegada de Marina, a passagem de plantão
com Almeida e o objetivo do diário. Um bilhete pede que ela escute e confira
os fatos antes de deixar o sistema decidir por ela. A leitura ocorre antes
do relógio e pode ser acelerada com ENTER; a seta esquerda volta uma página.

**Desenvolvimento:** o jogador alterna cuidados e observação. Após a primeira
entrega, ouve um relato que pode guardar. Uma visita posterior à farmácia
revela uma ficha de 1991: o mesmo relato foi riscado e substituído por SEM
OCORRÊNCIAS. Quando as câmeras apagam, a prévia do VIGIA continua negando
incidentes. As batidas e a aparição colocam em dúvida a confiabilidade do sistema.

**Conclusão:** chegar ao amanhecer resolve o objetivo de cuidado. A tela do
relatório apresenta os registros guardados, que podem ser relidos por clique,
e duas ações: anexar o diário e contestar o relatório, ou assinar o relatório
automático. O epílogo encerra a decisão de Marina, mantendo o mistério da presença.

Se a estabilidade de alguém chegar a zero, a partida termina com o relatório
de derrota já existente. A história não apresenta a escolha do amanhecer nesse caso.

## Registros opcionais

| Registro | Como descobrir | O que acrescenta |
|---|---|---|
| O relato ouvido | Concluir a primeira entrega válida a qualquer um dos pacientes | Um testemunho relaciona batidas e falhas de luz |
| A ficha de 1991 | Visitar CAM 05 após 90s, com sinal e livre para interagir | Um relato semelhante já foi apagado do arquivo |
| O apagão omitido | O blecaute realmente ocorrer durante o turno | A própria falha técnica contradiz a prévia automática |

Descobrir deixa o registro pendente. F ou o botão **Guardar registro** salva
o mais antigo ainda não guardado. Uma visita ou um atendimento repetido não
duplica a descoberta. Não há prazo específico, pontos de cura ou penalidade
por ignorar o diário. É possível sobreviver sem guardar nenhum registro.

Guardar funciona durante o plantão, com as interações disponíveis; fica
bloqueado no protocolo, susto e transição. Um apagão já descoberto pode ser
anotado mesmo sem sinal. O diário não usa a bandeja de medicamentos.

As descobertas e a decisão pertencem ao turno atual e são limpas ao recomeçar.
Não há coleção persistente entre partidas nesta versão.

## Desfechos implementados

| Escolha | Registros guardados | Epílogo |
|---|---|---|
| Contestar com o diário | 2 ou 3 | **Uma noite registrada**: Marina preserva uma cópia e Almeida assina como testemunha; há material para comparar os arquivos |
| Contestar com o diário | 0 ou 1 | **O primeiro testemunho**: Marina recusa a conclusão automática, mas reconhece as lacunas da documentação |
| Assinar a versão automática | Qualquer quantidade | **Sem ocorrências**: a versão oficial omite as dúvidas; ao sair, Marina volta a ouvir as batidas |

Os dois pacientes chegam ao amanhecer em todas essas variantes. O texto
considera quantos registros foram realmente guardados. Não atribui ao jogador
provas que ele não coletou.

## Marcação do turno

A noite tem 360 segundos reais e representa 00h00–06h00. Na duração atual,
um segundo real equivale a um minuto do relógio fictício. As falas aguardam
na fila quando outra ainda está em exposição ou o protocolo cobre a tela.

| Tempo real | Acontecimento narrativo ou de ambiente |
|---|---|
| Antes do relógio | Chegada, orientação de Almeida e bilhete |
| 5s | Rádio identifica os pacientes e orienta Marina a anotar discrepâncias |
| 20s | Primeiro pedido guiado, que pode levar ao primeiro relato |
| 40s | Luzes oscilam; três batidas e comentário de Daniel |
| 76s | Almeida menciona uma ficha deixada na farmácia |
| A partir de 90s | Visitar a farmácia permite descobrir a ficha |
| 120s e 230s | Relatos de sombra; alarmes e necessidade de observar a estabilidade |
| 165s | Prévia do VIGIA classifica relatos como falhas de percepção |
| 215s | Marina decide conferir o que o sistema omite |
| 260s | Apagão real e descoberta da omissão |
| 292s | Almeida reconhece o padrão nos arquivos antigos |
| 300s | Batidas e interferência na CAM 02 |
| 330s | Aparição no sinal: susto roteirizado |
| 338s | Marina distingue a imagem dos pacientes e retoma o objetivo |
| 351s | Aviso de que a assinatura será solicitada |
| 360s | Decisão do relatório e epílogo, se o atendimento chegar ao fim |

## Como a narrativa participa da gameplay

O relato vem de um atendimento concluído, por isso cuidar também aproxima
Marina das pessoas envolvidas no mistério. A ficha está na farmácia, local
que já faz parte do trajeto dos pedidos. O apagão já afeta o monitoramento e
passa a servir também como evidência. A investigação acrescenta uma escolha
ao fim do turno sem criar mais um prazo concorrendo com os medicamentos.

A legenda aguarda quando o protocolo bloqueia a leitura. Isso não pausa a
estabilidade, os pedidos ou o relógio. Falas importantes entram em fila;
agradecimentos repetidos cedem espaço. Os registros podem ser relidos no final.

## Explicação curta para a apresentação

Turno Noturno coloca o jogador no papel de uma pesquisadora que acompanha
dois pacientes por câmeras em um hospital de 1996. Para terminar o plantão,
é preciso observar, realizar protocolos e entregar medicamentos. Durante
essas ações, o jogador encontra relatos e arquivos que contradizem o relatório
automático. A história tem uma abertura, descobertas durante a partida e uma
decisão final que muda o epílogo. Assim, cuidar dos pacientes e descobrir o
mistério fazem parte do mesmo turno.

## Onde editar e o que ainda depende de playtest

- `story.py`: textos, personagens, momentos de fala, condições e epílogos.
- `story_ui.py`: páginas de abertura, faixa de rádio, diário e escolha final.
- `nights.py` / `event_manager.py`: eventos de câmera, luzes, som e susto.
- `ARTE_E_PROMPTS.md`: origem da arte e orientação para trocar o jumpscare.

Esta versão já funciona com texto, sons e imagem. Não inclui dublagem,
cutscene animada nem Noite 2. Para testar com pessoas, observar se conseguem
ler enquanto cuidam, entendem a diferença entre descobrir e guardar, e
chegam ao final compreendendo a decisão. Os testes automáticos verificam
a integração, mas não medem compreensão da história ou dificuldade humana.
