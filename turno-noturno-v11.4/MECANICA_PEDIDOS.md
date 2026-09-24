# Farmácia e pedidos — implementado

O objetivo é criar uma razão concreta para abandonar temporariamente a
observação: ouvir um paciente, buscar o que ele pediu e voltar para entregar,
enquanto o outro continua precisando de atenção.

## Fluxo

Chamado → câmera do paciente + R → lista no painel → F5 / farmácia →
retirar itens → reencontrar o paciente → R para entregar.

O chamado informa o canal de origem naquele instante. Movimentos posteriores
não são revelados automaticamente. A lista continua visível, e o último
contato só muda ao observar o paciente novamente. O primeiro atendimento
mantém o Paciente 02 na mesma sala para ensinar a sequência.

| Código | Nome fictício | Símbolo | Atalho na farmácia |
|---|---|---|---|
| A | Lume | círculo | Q |
| B | Aster | triângulo | W |
| C | Nimbo | quadrado | E |
| D | Vesper | losango | Z |
| E | Orbe | cruz | X |
| F | Nexo | duas barras | C |

Os medicamentos têm identidades visuais diferentes e a mesma função de jogo:
completar o pedido. Não há receitas, dosagens, efeitos reais ou combinações
ocultas. Alterar nomes e cores requer só editar `MEDICINES` em `medication.py`.

## Valores iniciais

| Regra | Valor |
|---|---|
| Primeiro chamado | 20s; Paciente 02; Lume; prazo de 70s |
| Pedidos simultâneos | 1 |
| Intervalo após resolver/expirar | aleatório entre 32 e 48s |
| Tamanho do pedido | 1, 2 ou 3 medicamentos diferentes |
| Chances por tamanho | 55%, 30%, 15% |
| Prazo normal | 30s, 40s, 50s |
| Recuperação | +14, +20, +26; limitada a 100 |
| Expiração | -18; o primeiro pedido não aplica essa penalidade |
| Bandeja | 3 espaços; esvazia ao entregar ou expirar |
| Protocolo | +50 após 4s; recarga individual de 25s |

Cada prazo cobre o atendimento inteiro, sem reiniciar ao ouvir o pedido.
O prazo do tutorial é generoso, mas a estabilidade normal continua caindo:
o jogador também precisa usar os protocolos e alternar as câmeras.
Não nasce um pedido sem tempo para seu prazo antes do amanhecer.

## Regras de interação

- Farmácia acessível por F5, abas ou A/D; pacientes circulam nas outras 4 salas.
- Só é possível retirar itens depois de ouvir o pedido. Não há pré-estoque.
- Bandeja não aceita itens duplicados nem um quarto item.
- Selecionar um item diferente do pedido é permitido. A entrega será recusada
  até a bandeja conter exatamente a lista. Não há punição extra pela tentativa.
- Clique em um item da bandeja para removê-lo; BACKSPACE remove o último.
- Ouvir/entregar exige paciente visível e câmera com sinal.
- Blecaute bloqueia coleta e entrega; protocolo bloqueia as interações.
- Protocolo não cancela nem completa pedido. O prazo continua correndo e
  aparece abaixo da janela do protocolo.
- Intervalo conta após resolução, impedindo pedidos em sequência imediata.
- O áudio e a lista dos chamados antigos foram removidos da lógica ativa;
  seus WAVs são reutilizados como avisos de pedido.

## Falas e explicação da derrota

Pacientes comentam o atendimento e relatam luzes/sombras ligadas ao roteiro.
A fala não distingue automaticamente um alarme falso de uma anomalia.
Não é necessário responder a um segundo tipo de chamado.

O primeiro pedido concluído também revela o relato que pode ser guardado no
diário com F. A farmácia contém uma ficha disponível depois de 90s de turno.
Investigar não altera a estabilidade nem substitui entrega ou protocolo.
Veja HISTORIA_E_ROTEIRO.md para as condições e o desfecho dessa investigação.

O histórico registra protocolos, deslocamentos, eventos e pedidos. Na derrota,
mostra apenas fatos da partida, até três eventos recentes relevantes, a causa
imediata de chegar a zero e o estado da recarga. Não inventa que um pedido foi
ignorado ou que houve um erro de timing quando isso não aconteceu.

## O que observar no playtest

1. Um jogador novo completa o primeiro pedido sem explicação externa?
2. A lista e o nome dos medicamentos estão legíveis no monitor da feira?
3. O intervalo de 32–48s dá espaço para cuidar dos dois pacientes?
4. Protocolos e entregas são usados juntos, sem um tornar o outro dispensável?
5. Procurar um paciente depois da coleta gera tensão ou frustração?
6. Após perder, o jogador consegue apontar a causa e planejar outra tentativa?

Os números ficam em `settings.py`. Ajuste uma variável de cada vez depois de
testar com pessoas: prazo para dificuldades na coleta, intervalo para excesso
de tarefas, recuperação para entregas pouco relevantes e movimento para
dificuldade de localizar pacientes.

## Validação técnica

Testes automatizados cobrem itens distintos, bandeja exata, recompensa única,
intervalo, tutorial, ações por teclado/mouse, câmera errada, movimento, blecaute,
protocolo em andamento, expiração e relatório. Há uma simulação de noite inteira
com os eventos do roteiro, sem modificar estabilidade durante o turno.
Ela conhece as salas atuais para navegar e não mede a dificuldade humana.

A build Windows deve ser gerada e aberta no Windows. O projeto mantém os
assets existentes e só usa pygame-ce no jogo; sem NumPy ou novas dependências.
