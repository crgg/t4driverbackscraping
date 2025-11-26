# app/writer.py
from pathlib import Path
from typing import Iterable


def save_logs(
    controlados: Iterable[str],
    no_controlados: Iterable[str],
    output_dir: str = "salida_logs",
    archivo_controlados: str = "errores_controlados.log",
    archivo_no_controlados: str = "errores_no_controlados.log",
    mode: str = "a",
) -> None:
    """
    Guarda los logs en dos archivos dentro de output_dir.
    mode='a' para ir añadiendo; usa 'w' si quieres sobrescribir.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    controlados_path = output_path / archivo_controlados
    no_controlados_path = output_path / archivo_no_controlados

    with controlados_path.open(mode, encoding="utf-8") as f:
        for line in controlados:
            f.write(line + "\n")

    with no_controlados_path.open(mode, encoding="utf-8") as f:
        for line in no_controlados:
            f.write(line + "\n")
