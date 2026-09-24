# Arte e áudio da revisão narrativa

## Jumpscare

Arquivo incluído: `assets/sprites/jumpscare.png`.

Modo de criação: geração de imagem original com a ferramenta integrada
ImageGen, sem imagem de referência. A imagem foi copiada para o projeto
sem retoque externo. Os fundos e sprites anteriores foram preservados.

A direção foi aproximar o susto da estética das câmeras: preto e branco,
rosto indistinto muito próximo, ruído de sinal e bordas escuras. A presença
não representa Daniel ou Elias. A imagem substitui o rosto de polígonos;
o código fica responsável por enquadramento, tremor e desaparecimento.

Prompt utilizado, integralmente:

```text
Use case: stylized-concept. Asset type: finished full-screen jumpscare still for a Brazilian hospital surveillance horror game set in 1996, replacing a crude geometric placeholder. Create one original eerie apparition seen extremely close through the glass of a failing CRT surveillance signal. Landscape 16:9 composition. Photographic analog-horror treatment, strictly black and white, deep black background merging into the edges, grainy low-light texture and subtle horizontal signal tearing. A single nonhuman, indistinct face occupies the central 60 percent of the frame: softly blurred stretched facial proportions, sunken dark eye sockets, faint pale eyes, mouth barely open in an unnatural silent expression; unsettling through proximity and expression, not through injury. The whole face is contained within the central safe area so a modest zoom does not crop its eyes. The sides disappear into darkness. Strong readable silhouette and facial contrast for a brief on-screen flash. It must look like an anomalous presence inside a video signal, not one of the hospital patients: no patient clothing, no medical gear, no recognizable person. No blood, no wounds, no gore, no exposed bones, no exaggerated rows of teeth. No polygons, no cartoon drawing, no red tint, no lettering, no interface, no frame, no watermark. The image itself fills the canvas; opaque background, not transparent.
```

Para usar uma ilustração feita pela equipe, substitua o mesmo PNG. Prefira
16:9 horizontal, fundo opaco e rosto na área central. O jogo preenche a tela
com crop central e mantém quatro escalas em cache. Não há filtro ou biblioteca
de imagem adicional em runtime. Se a imagem não carregar, o susto mostra
SINAL PERDIDO até o retorno ou a tela de derrota.

## Três batidas

Arquivo incluído: `assets/sounds/knocks.wav`.

Som sintetizado por `tools/generate_placeholder_audio.py`, usando apenas
a biblioteca padrão do Python. Há três pulsos amortecidos ao longo de 1,1s,
em WAV mono, PCM 16-bit, 22050 Hz. O som acompanha a oscilação de luz aos
40s e o evento do corredor aos 300s.

O gerador só cria arquivos ausentes. Para usar uma gravação própria, troque
o WAV mantendo o nome. O jogo apenas carrega o arquivo; não sintetiza áudio
durante a partida e continua sem NumPy.

## Demais visuais

As novas telas usam a interface de janelas já existente. O diário e as falas
fazem parte do VIGIA, com texto maior, caixas claras e escolhas por teclado
ou mouse. Os cenários, sprites de pacientes e sons anteriores permanecem
no pacote. A farmácia continua usando as prateleiras desenhadas pela interface.
