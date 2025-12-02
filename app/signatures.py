# app/signatures.py
import re

# Tokens a partir de los cuales ya no nos importa el resto del mensaje
_CUT_TOKENS = [
    "[stacktrace]",
    '{"Request :',
    "Accept:",
    "Host:",
    "User-Agent:",
]

_SQLSTATE_RE = re.compile(r"(SQLSTATE\[[0-9A-Z]+\])")


def build_signature(line: str) -> str:
    """
    Construye una firma estable para un error a partir de la línea completa.
    La idea es que errores "iguales" generen la misma firma aunque
    cambien detalles (IDs, stacktrace, headers, etc).
    """
    msg = line

    # Cortar por tokens conocidos
    for token in _CUT_TOKENS:
        idx = msg.find(token)
        if idx != -1:
            msg = msg[:idx]

    # Cortar al final del SQLSTATE si existe
    m = _SQLSTATE_RE.search(msg)
    if m:
        msg = msg[: m.end()]

    return msg.strip()
