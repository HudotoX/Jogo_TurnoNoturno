# Correções da versão 11.2

## Revisão atual — história, arte e interface

- História da Noite 1 implementada no Hospital Nossa Senhora da Piedade,
  em 1996: Marina Duarte, Almeida, Daniel (01), Elias (02) e os relatórios do VIGIA.
- Três páginas de abertura, com avanço/retorno por teclado e mouse. O relógio
  do plantão só começa após a leitura.
- Falas durante o turno ligadas ao atendimento e aos acontecimentos, com
  fila que preserva a exposição do texto quando a tela de protocolo o cobre.
- Três descobertas opcionais: relato após entrega, ficha antiga na farmácia
  e apagão omitido. F ou botão guarda uma por vez, sem cura nem pausa.
- Amanhecer abre a decisão do relatório. Registros podem ser relidos; duas
  escolhas e a quantidade guardada determinam três variantes de epílogo.
- Arte original de aparição em PNG substitui o rosto de polígonos. Frames
  preparados em cache, preenchimento da tela e tremor; sem nova dependência.
- Novo WAV de três batidas acompanha dois eventos do roteiro.
- Barras dos pacientes maiores, valor visível na leitura atual e textos com
  mais contraste. Última leitura continua sem revelar estado atual fora da câmera.
- X do protocolo agora cancela corretamente com recarga de 6s, preservando
  pedido e bandeja.
- Roteiro documentado em HISTORIA_E_ROTEIRO.md; origem da arte em ARTE_E_PROMPTS.md.
- 40 testes passaram em Python 3.12 / pygame-ce 2.5.8, sem NumPy; inclui turno
  completo com os três registros e a decisão final. Telas conferidas em 1280×720.
- Build de verificação gerada com PyInstaller no Linux: inicialização sem erro,
  imagem e som novos incluídos, sem arquivos do NumPy no pacote.
  A geração e abertura do executável Windows ainda precisam ocorrer no Windows.

## Revisão anterior — farmácia e pedidos

- Adicionada CAM 05 / F5: Ala Farmacêutica, seis medicamentos fictícios
  identificados por código, nome, cor e símbolo, bandeja de três itens.
- Primeiro chamado aos 20s, com um item, instruções, prazo de 70s e sem
  penalidade por expiração. O paciente permanece na sala nesse atendimento.
- Pedidos de 1–3 itens distintos, um ativo por vez, intervalo de 32–48s
  após resolução. Pedidos maiores têm mais prazo e recuperação.
- Chamados antigos foram substituídos. O protocolo não resolve pedidos,
  e todos os timers continuam contando enquanto ele está aberto.
- Entregas exigem paciente visível, bandeja exata e câmera com sinal.
  Itens podem ser removidos; não há duplicatas nem estoque para o futuro.
- Corrigido multiplicador indevido de 10 na chance de movimento. Após
  mover-se, o paciente fica ao menos 8s antes de outro movimento aleatório.
  A farmácia não é destino de pacientes.
- Incluídos comentários dos pacientes ao receber pedidos/entregas e falas
  ligadas às luzes e sombras do roteiro.
- Derrota mostra a causa real, paciente(s), horário, situação do protocolo
  e três acontecimentos recentes. Novo turno limpa histórico e bandeja.
- UI da farmácia e atendimento revisada em 1280×720; controles por teclado
  e mouse e regressões de pedidos/protocolos cobertos por testes.
- Tags nas câmeras mostram o número completo do paciente, facilitando a entrega.
- Dependência de runtime continua apenas pygame-ce, sem NumPy.

## Revisão anterior — protocolo preventivo / sem NumPy

- A regra abaixo de 25 descrita no histórico foi substituída: qualquer
  estabilidade acima de zero permite uso, com paciente visível e sem recarga.
- Cooldown individual: 25s após sucesso, 6s após cancelamento. Segurar por 4s;
  perda durante protocolo: 1 ponto/s; recuperação: +50, limitada a 100.
- A recomendação aparece em 55, mas não é pré-requisito. HUD mostra recarga
  mesmo sem sinal, sem revelar estabilidade nem localização atuais.
- Removidos NumPy, síntese de áudio em runtime e código morto do filtro antigo.
  O grayscale é do Pygame. Nove WAVs de teste completam os sete sons existentes.
- Corrigida cobrança dupla de decaimento no frame de conclusão e removido bônus
  de observação enquanto a tela de protocolo bloqueia as câmeras.
- O glow respeita a opacidade e não estoura mais os brancos; removidos controles
  legados de filtro que já não tinham efeito. Abas rotuladas com F1–F4.
- Adicionados testes de regressão e gerador opcional de áudio só com biblioteca
  padrão. A proposta de interfone é documentação, não mecânica instalada.

## Histórico anterior (substituído pelos itens acima quando houver conflito)

- Câmeras diretas migradas de `1–4` para `F1–F4`; `1/2` ficaram exclusivos
  para os protocolos dos pacientes.
- O protocolo não pausa mais o relógio, o outro paciente, chamados, eventos,
  interferências ou blecautes.
- Um protocolo só pode começar com estabilidade de 25 ou menos e enquanto o
  paciente estiver realmente visível na câmera ativa.
- A HUD guarda `last_known_room` e não revela movimentos que ainda não foram
  observados.
- A janela agora se adapta à resolução disponível, aceita redimensionamento e
  alterna tela cheia com `F11`, mantendo o canvas 16:9 sem distorção.
- Incluído fluxo de build com PyInstaller (`build_windows.bat` e
  `turno_noturno.spec`); `jogar.bat` prioriza a build pronta.
- A build agora usa um ambiente virtual isolado e `pygame-ce 2.5.8`, com wheel
  pronta para Python 3.14 no Windows; instalações por código-fonte são
  bloqueadas para evitar falhas de SDL/distutils.
- Fundos preservam a proporção com crop central; fundos, sprites e overlays do
  CRT usam cache, e a conversão P&B ocorre apenas no carregamento.
- O áudio de perigo toca somente na entrada do estado `PERIGO`, com uma segunda
  proteção por cooldown.
- Placeholders sonoros agora funcionam tanto com mixer mono quanto estéreo.
- Os quatro cenários `.png` e `static_burst.wav` foram convertidos para os
  formatos indicados pelas extensões.
