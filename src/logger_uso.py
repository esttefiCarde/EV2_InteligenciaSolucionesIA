"""Registro de consultas SIN datos personales (la pregunta se guarda enmascarada)."""
import json
import time
from .config import LOG_PATH


def registrar(evento: dict, ruta=LOG_PATH) -> None:
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        evento = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **evento}
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False) + "\n")
    except OSError:
        pass  # el registro nunca debe romper la atención al estudiante
