# app/notifier.py
from typing import Dict, Any

from app.email_notifier import enviar_resumen_por_correo


def notificar_app(resultado: Dict[str, Any]) -> None:
    """
    Recibe el dict devuelto por procesar_aplicacion()
    y envía el correo correspondiente.
    """
    dia = resultado["dia"]
    app_name = resultado["app_name"]
    app_key = resultado["app_key"]

    enviar_resumen_por_correo(dia, app_name, app_key)
    print(f"✓ Correo enviado para {app_name}")
