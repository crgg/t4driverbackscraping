# app/error_filter.py
from datetime import date
from typing import List, Tuple

from db import get_alerted_signatures, add_alerted_signatures
from .signatures import build_signature


def dividir_nuevos_y_avisados(
    lineas: List[str],
    app_key: str,
    dia: date,
    tipo: str,  # 'controlado' o 'no_controlado'
) -> Tuple[List[str], List[str]]:
    """
    Separa las líneas en:
      - nuevas: nunca avisadas antes en el día
      - avisadas: ya avisadas al menos una vez hoy

    Además, marca las nuevas como avisadas en la BD.
    """
    ya_avisadas = get_alerted_signatures(app_key, dia, tipo)

    nuevas: List[str] = []
    avisadas: List[str] = []
    nuevas_firmas = set()

    for linea in lineas:
        firma = build_signature(linea)
        if firma in ya_avisadas:
            avisadas.append(linea)
        else:
            nuevas.append(linea)
            nuevas_firmas.add(firma)

    # Persistimos las nuevas firmas como "ya avisadas"
    if nuevas_firmas:
        add_alerted_signatures(app_key, dia, tipo, nuevas_firmas)

    return nuevas, avisadas
