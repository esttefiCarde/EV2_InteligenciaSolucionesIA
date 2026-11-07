"""Agente coordinador: clasifica la consulta en un área (LLM + respaldo por reglas)."""
import json
import re
from typing import Callable, Optional

from .config import AREAS, UMBRAL_ROUTER
from .guardrails import normalizar
from .prompts import ROUTER_SYSTEM, ROUTER_USER

PALABRAS = {
    "academico": ["asignatura", "ramo", "reprueb", "repet", "nota", "examen", "evaluacion",
                  "asistencia", "inasistencia", "justificar", "eliminacion", "reglamento",
                  "apelacion", "promedio", "solemne", "malla", "semestre", "prueba"],
    "administrativo": ["certificado", "alumno regular", "concentracion", "tramite", "solicitud",
                       "matricula", "arancel", "pago", "tne", "suspension", "retiro",
                       "punto estudiantil", "beca", "cuota", "documento de"],
    "practica_titulacion": ["practica", "titulacion", "titulo", "titularme", "proyecto de titulo",
                            "empresa", "supervisor", "seguro de practica", "horas de practica",
                            "informe final", "examen de titulo"],
    "ti": ["contrasena", "clave", "intranet", "compass", "ava", "aula virtual", "correo",
           "plataforma", "no puedo ingresar", "no puedo entrar", "error", "wifi", "login",
           "acceso", "sistema caido", "office", "teams", "bloqueada", "bloqueado"],
}


def clasificar_por_palabras(texto: str) -> tuple:
    """Clasificador de respaldo. Devuelve (area, confianza 0-1) o ('otro', 0.0)."""
    n = normalizar(texto)
    puntajes = {a: sum(1 for p in ps if p in n) for a, ps in PALABRAS.items()}
    mejor = max(puntajes, key=puntajes.get)
    total = sum(puntajes.values())
    if puntajes[mejor] == 0:
        return "otro", 0.0
    return mejor, round(puntajes[mejor] / total, 2)


def parsear_router(salida: str) -> Optional[dict]:
    """Extrae el JSON de la respuesta del LLM (tolera ```json y texto extra)."""
    if not salida:
        return None
    m = re.search(r"\{.*\}", salida, flags=re.DOTALL)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    area = str(d.get("area", "")).strip().lower()
    if area not in AREAS and area != "otro":
        return None
    try:
        conf = float(d.get("confianza", 0))
    except (TypeError, ValueError):
        conf = 0.0
    return {"area": area, "confianza": max(0.0, min(conf, 1.0)),
            "carrera": d.get("carrera") or None, "motivo": d.get("motivo", "")}


def clasificar(texto: str, generar: Optional[Callable[[str, str], str]] = None) -> dict:
    """Clasifica con el LLM; si falla o duda, usa/combina el respaldo por reglas."""
    reglas_area, reglas_conf = clasificar_por_palabras(texto)
    if generar is None:
        return {"area": reglas_area, "confianza": reglas_conf, "carrera": None,
                "motivo": "clasificador por reglas"}
    try:
        res = parsear_router(generar(ROUTER_SYSTEM, ROUTER_USER.format(pregunta=texto)))
    except Exception:  # error de red, cuota, etc.
        res = None
    if res is None:
        return {"area": reglas_area, "confianza": reglas_conf, "carrera": None,
                "motivo": "respaldo por reglas (LLM no disponible)"}
    if res["confianza"] < UMBRAL_ROUTER and reglas_conf >= 0.6:
        res.update(area=reglas_area, motivo="baja confianza LLM; se usa regla")
    return res
