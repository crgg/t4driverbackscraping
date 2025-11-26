# app/email_notifier.py
from datetime import date
from typing import List, Tuple

from .alerts import send_email, default_recipients
from .log_stats import (
    NO_CONTROLADOS_PATH,
    CONTROLADOS_PATH,
    resumen_por_fecha,
    url_logs_para_dia,
)


def _html_lista(titulo: str, items: List[Tuple[str, int]]) -> str:
    if not items:
        return f"<h3>{titulo}</h3><p>Sin elementos.</p>"

    lineas = [f"<h3>{titulo}</h3>", "<ul>"]
    for firma, count in items:
        firma_corta = firma if len(firma) <= 400 else firma[:400] + "..."
        lineas.append(f"<li><strong>{count}×</strong> — {firma_corta}</li>")
    lineas.append("</ul>")
    return "\n".join(lineas)


def construir_html_resumen(dia: date) -> tuple[str, int, int]:
    total_nc, repetidos_nc, nuevos_nc = resumen_por_fecha(NO_CONTROLADOS_PATH, dia)
    total_c, repetidos_c, nuevos_c = resumen_por_fecha(CONTROLADOS_PATH, dia)

    url_logs = url_logs_para_dia(dia)

    partes = [
        f"<h2>Resumen de errores DriverApp — {dia.isoformat()}</h2>",
        f"<p>Total errores <strong>NO controlados</strong> hoy: <strong>{total_nc}</strong></p>",
        f"<p>Total errores <strong>controlados</strong> hoy: <strong>{total_c}</strong></p>",
        _html_lista("NO controlados repetidos hoy (>=3 veces)", repetidos_nc),
        _html_lista("NO controlados NUEVOS hoy", nuevos_nc),
        _html_lista("Controlados repetidos hoy (>=3 veces)", repetidos_c),
        _html_lista("Controlados NUEVOS hoy", nuevos_c),
        f'<p>Más detalles: <a href="{url_logs}">{url_logs}</a></p>',
    ]

    return "\n".join(partes), total_nc, total_c


def enviar_resumen_por_correo(dia: date) -> None:
    html, total_nc, total_c = construir_html_resumen(dia)

    # Si no hay errores, ni molestamos
    if total_nc == 0 and total_c == 0:
        return

    subject = f"[DriverApp] Errores {dia.isoformat()} — NC:{total_nc} / C:{total_c}"

    recipients = default_recipients()  # usa ALERT_EMAIL_TO o MAIL_USERNAME

    send_email(subject, html, recipients)
