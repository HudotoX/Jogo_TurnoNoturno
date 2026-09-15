# Turno Noturno — site do jogo

Site de divulgação/download do jogo **Turno Noturno**, feito para ficar no
mesmo repositório do GitHub que o código do jogo (Pygame) e ser publicado
com **GitHub Pages**.

## Estrutura sugerida do repositório

```
turno-noturno/                 ← repositório no GitHub
├── index.html                 ← site (raiz, pra Pages funcionar sem configuração extra)
├── styles.css
├── script.js
├── assets/
│   └── screenshots/
│       ├── cam-01-ala-descanso.png
│       ├── cam-02-corredor.png
│       └── cam-04-patio.png
└── jogo/                       ← código-fonte do jogo em Pygame
    ├── main.py
    ├── requirements.txt
    └── ...
```

O site fica na **raiz** do repositório de propósito: o GitHub Pages, no modo
mais simples, publica exatamente o que está na raiz da branch escolhida —
sem precisar de build, sem precisar mexer em configuração.

## Passo a passo — publicar com GitHub Pages

1. **Crie o repositório no GitHub** (se ainda não existe). Pode ser público.

2. **Coloque os arquivos do site na raiz do repositório** (os 3 arquivos
   `index.html`, `styles.css`, `script.js` e a pasta `assets/`, exatamente
   como estão nesta pasta) e o código do jogo dentro de uma subpasta, por
   exemplo `jogo/`.

3. **Suba tudo pro GitHub** (pelo terminal ou pelo GitHub Desktop):
   ```bash
   git add .
   git commit -m "adiciona site e jogo"
   git push
   ```

4. No repositório, vá em **Settings → Pages**.

5. Em **Source**, escolha a branch `main` e a pasta `/ (root)`. Clique em
   **Save**.

6. Espere ~1 minuto. O GitHub mostra o link do site no topo da mesma página
   (algo como `https://seu-usuario.github.io/turno-noturno/`). Pronto — o
   site está no ar, e toda vez que vocês derem `git push` de novo, ele
   atualiza sozinho.

## Como disponibilizar o jogo pra download

Pygame não roda direto no navegador, então o "download" é o jogo de verdade
(os arquivos `.py` zipados, ou um `.exe` se vocês empacotarem com algo como
`pyinstaller`). O jeito recomendado de disponibilizar isso no GitHub:

1. No repositório, vá em **Releases** (barra lateral direita) → **Create a
   new release**.
2. Dê um nome/tag pra versão (ex: `v0.1`).
3. Anexe o `.zip` do jogo (ou o `.exe`) em **Attach binaries**.
4. Publique a release. O GitHub gera um link direto de download pra esse
   arquivo.
5. Copie esse link e cole no `index.html`, no botão de download — procure
   por `id="download-link"` e troque o `href="#"` pelo link da release.

Também vale trocar o `href="#"` do link **"Ver código no GitHub"**
(`id="repo-link"`) pelo link real do repositório.

## O que personalizar

Procure por `EDITAR` dentro do `index.html` — são os 3 pontos que precisam
da informação de vocês:
- link de download do jogo
- link do repositório
- nome da equipe (na barra de status, embaixo)

O resto (textos, protocolo, capturas de tela) já está pronto, mas é só
texto normal em HTML — fiquem à vontade pra ajustar a descrição do jogo,
trocar as capturas de tela por outras mais atuais, etc.
