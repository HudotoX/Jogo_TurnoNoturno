# Turno Noturno — site 4.0

Site de divulgação alinhado ao conteúdo da **v12 do jogo**. O número 4.0 é a versão do site; não altera a versão do jogo.

## Abrir

Extraia a pasta inteira e abra `index.html` no navegador. Não precisa instalar nada, rodar comandos ou ter internet. Mantenha `assets`, `styles.css`, `config.js` e `script.js` ao lado do HTML.

## O que mudou

- Identidade inspirada no VIGIA: janelas cinza, barras azuis, imagens pixelizadas e textos nítidos.
- História: Marina Duarte, Daniel, Elias e Hospital Nossa Senhora da Piedade, em 1996.
- Uma Noite 1 de três minutos, cinco câmeras, farmácia, pedidos, protocolo de quatro segundos e investigação opcional.
- Controles completos de teclado e explicação do uso do mouse.
- Galeria das cinco câmeras, ampliação de imagem, navegação por teclado e adaptação a celulares.
- Efeitos sutis que podem ser desativados, respeito a movimento reduzido, foco visível e diálogo acessível.
- Sem fontes remotas, bibliotecas, rastreadores ou reprodução automática de som.

## Habilitar o download quando houver um link

Abra `config.js` num editor de texto e preencha `downloadUrl` com o endereço público real da versão v12. Opcionalmente, preencha `repositoryUrl` com o repositório. `downloadDescription` deve descrever o pacote oferecido (por exemplo, executável Windows ou código-fonte com instruções).

Enquanto os campos estiverem vazios, o site mostra que o download ainda não está disponível e oculta o link do repositório. Não há botões com destinos falsos. Os endereços devem começar com `https://` ou `http://`. Caminhos do computador e links `sandbox:` dos chats não são links públicos.

O site pode ser hospedado como arquivos estáticos. Publique todo o conteúdo desta pasta junto e preserve os caminhos relativos. Esta entrega não foi publicada na internet.

## Referências e imagens

As informações da v12 (noite de três minutos, até três pedidos, controle por mouse e teclado e pixelização fixa) foram recuperadas do chat **Opinião sobre pixelização**, do projeto SNCT. A história e as mecânicas também foram conferidas no chat **Análise do projeto de jogo** e no código/documentação local da v11.4. O chat **Cartaz do jogo** esclarece a inspiração em Nise da Silveira e que o foco da divulgação é o jogo.

As imagens em `assets/vigia` foram renderizadas diretamente pela interface da **v11.4 disponível no computador**, com a pixelização fixa em 30%, sem editar os arquivos originais do jogo. Elas mostram as cinco câmeras e o estilo de interface que o histórico da v12 informa ter mantido. Não são capturas de uma execução da v12: o arquivo desse jogo não estava disponível localmente. A duração de seis minutos da v11.4 não foi transportada para os textos do site.

Quando houver novas capturas da v12, elas podem substituir `cam-01.png` até `cam-05.png` (16:9, preferencialmente 1920 × 1080). `feed-01.png` é a imagem de destaque. Atualize o texto alternativo caso o conteúdo visual mude.

Os arquivos originais do ZIP do site 3.0 e do jogo foram preservados.
