# Proposta para debate: interfone e refúgio temporário

Status: ARQUIVADO / NÃO IMPLEMENTADO. A proposta foi substituída pela
mecânica de pedidos aprovada e implementada em `MECANICA_PEDIDOS.md`.
O texto abaixo permanece somente como histórico da discussão.

## O que muda para o jogador

Além de monitorar e recuperar estabilidade, o jogador pode orientar um
paciente para outra sala. Isso cria decisões de posição e de prioridade:
quem mover, por qual caminho e qual câmera deixar de acompanhar enquanto isso.
O problema não é só a barra do paciente: algo no ambiente do hospital piora
sua condição, e o jogador pode intervir antes da crise.

## Protótipo mínimo

- Um botão de interfone na câmera que mostra o paciente; escolher uma sala
  vizinha entre botões rotulados. Se houver dois pacientes, selecionar um.
- Movimento por ligação explícita entre salas, nunca teletransporte aleatório.
  Por exemplo: descanso — corredor — observação, e corredor — pátio.
- Deslocamento de cerca de 3 segundos. Exibir "deslocamento em andamento",
  mas só atualizar a localização conhecida quando reencontrar o paciente.
- Uma sala com recurso de conforto para uma pessoa por vez. Por cerca de 15s,
  reduz o decaimento, sem recuperar pontos nem substituir o protocolo.
- A sala precisa de recarga antes de oferecer novo conforto. O paciente não
  ganha proteção só por entrar e sair: o efeito é limitado por uso da sala.
- Uma ocorrência roteirizada pode tornar uma sala inadequada temporariamente:
  luz oscilando, ruído ou sombra. Sempre há aviso e tempo de reação.

## Uma decisão concreta

O paciente 02 precisa de cuidado, mas o protocolo dele ainda está em recarga.
O paciente 01 já ocupa o refúgio e está relativamente estável. Vale mover o 01
para liberar o recurso? Há ruído no corredor: talvez seja melhor esperar ou
concluir primeiro o atendimento que já está disponível.

O objetivo é criar alternativas, não fazer o jogador decorar uma ordem fixa
de botões. O refúgio nunca deve virar uma solução de "estacionar os dois e
esperar", e falhar no interfone não deve causar morte instantânea.

## Implementação no projeto existente

1. `settings.py`: ligações entre salas, duração do trajeto, redução de
   decaimento e recarga do refúgio.
2. `patient.py`: `destination_room`, `travel_timer`, início/fim do movimento.
   Um comando em andamento impede a movimentação aleatória de atropelá-lo.
3. `camera_system.py`: estado de cada sala (normal, refúgio ativo, recarga,
   ocorrência) e uso dos cenários atuais com overlays simples.
4. `game.py` e `ui.py`: seleção de paciente/destino, validação da ligação,
   mensagens claras e integração com os timers que já continuam no protocolo.
5. `event_manager.py`: um evento ambiental anunciado para ensinar a decisão;
   não acrescentar vários tipos de anomalia antes de testar o primeiro.

## Como saber se melhorou

- Em até 30 segundos um jogador novo consegue explicar por que moveu alguém?
- Usa protocolo e interfone em situações diferentes, ou um substitui o outro?
- Uma derrota permite entender o erro e pensar numa alternativa?
- Ficar parado numa câmera deixa de ser uma estratégia suficiente?

Um teste com duas ou três pessoas sem contato prévio com o jogo será mais
informativo que acrescentar outra noite. Registrar falhas e hesitações; não
ensinar as regras durante o teste, exceto se o protótipo realmente bloquear.

## Outros polimentos para discutir

- Um chamado guiado nos primeiros 15–20s, sem penalidade severa na primeira vez.
- Tela de derrota com os últimos acontecimentos e causa específica.
- Sinais de sala que os pacientes percebem antes do sistema: reforça a ideia
  de que eles precisam de ajuda e informação, não de que são os monstros.
- Testar o protocolo preventivo sozinho antes de colocar o interfone, para
  identificar de onde vem cada melhoria ou novo problema de dificuldade.
