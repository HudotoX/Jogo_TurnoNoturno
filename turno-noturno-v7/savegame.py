"""
savegame.py
Persistência mínima de progresso: só guarda a mais alta noite já
desbloqueada (não estado no meio de uma noite — cada noite dura poucos
minutos, não compensa salvar estado parcial). É o suficiente pra
garantir que perder a Noite 2 não obrigue a rejogar a Noite 1.

Arquivo salvo como JSON ao lado do próprio jogo. Qualquer falha de
leitura/escrita (permissão, disco, arquivo corrompido) é tratada em
silêncio e cai no progresso padrão — um save quebrado nunca deve
impedir o jogo de abrir.
"""

import json
import os
import sys
import settings as cfg


def _application_dir():
    """Pasta persistente tanto no código-fonte quanto no executável."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)


SAVE_PATH = os.path.join(_application_dir(), cfg.SAVE_FILE_NAME)

DEFAULT_PROGRESS = {"unlocked_night": 1}


def load_progress():
    """Retorna um dict {'unlocked_night': int}. Nunca lança exceção."""
    if not os.path.isfile(SAVE_PATH):
        return dict(DEFAULT_PROGRESS)
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        unlocked = max(1, int(data.get("unlocked_night", 1)))
        return {"unlocked_night": unlocked}
    except (OSError, ValueError, json.JSONDecodeError, TypeError):
        return dict(DEFAULT_PROGRESS)


def save_progress(unlocked_night):
    """Atualiza o save apenas se a nova noite for maior que a salva —
    nunca "regride" o progresso por engano."""
    current = load_progress()
    if unlocked_night <= current["unlocked_night"]:
        return
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump({"unlocked_night": unlocked_night}, f)
    except OSError:
        pass  # progresso não persiste nesta sessão, mas o jogo continua normal


def reset_progress():
    try:
        if os.path.isfile(SAVE_PATH):
            os.remove(SAVE_PATH)
    except OSError:
        pass
