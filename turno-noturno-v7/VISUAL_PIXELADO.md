# Visual pixelizado — v11.4

As câmeras e o jumpscare usam pixelização **fixa em 30%**. Cenário e pacientes
são compostos juntos, reduzidos para 30% da largura e da altura do quadro e
ampliados sem interpolação. Textos, botões, legendas, nomes e indicadores são
desenhados em resolução normal.

Não há seletor no menu nem atalho F6. O antigo `video_turno_noturno.json`
não é lido nem gravado; uma preferência da v11.3 não muda o visual desta versão.
Os PNGs originais continuam intactos. As linhas do monitor permanecem discretas.

O efeito está em `video_effects.py`, usado por `camera_system.py` e `ui.py`.
O valor fixo fica em `settings.py`, em `PIXEL_SCALE = 0.30`. Os quatro frames
de zoom do jumpscare são preparados antes do susto, sem redimensionar a arte
a cada frame. A adaptação da janela preserva a leitura em telas menores.

As capturas em `previas` mostram o menu, o jogo e o novo protocolo por mouse.
