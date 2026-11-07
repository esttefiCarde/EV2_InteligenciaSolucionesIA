"""Extracción de datos de la consulta con reglas (carrera, porcentajes, asistencia y notas).

Se usa cuando no hay LLM y para completar o verificar los argumentos que propone el LLM. Todo es
determinista: los datos personales que se extraen se usan en el turno y no se guardan."""
import re
from typing import Optional

from .guardrails import normalizar

# Sinónimos ordenados del más específico al más general
SINONIMOS_CARRERA = (
    ("Ingeniería en Informática", ("ingenieria en informatica", "ing. en informatica", "ing en informatica",
                                   "informatica")),
    ("Analista Programador", ("analista programador", "analista")),
    ("Ingeniería en Administración", ("ingenieria en administracion", "ing. en administracion",
                                      "ing en administracion", "administracion de empresas", "administracion")),
    ("Contabilidad General", ("contabilidad general", "contabilidad", "contador")),
    ("Enfermería", ("enfermeria",)),
)
_DECLARA_CARRERA = re.compile(
    r"\b(soy de|soy estudiante de|soy alumn[oa] de|estudio|mi carrera es|estoy en|curso|"
    r"me cambie a|me cambie de carrera a|ahora estudio|ahora soy de)\b")


def normalizar_carrera(texto: Optional[str]) -> Optional[str]:
    if not texto:
        return None
    n = normalizar(texto)
    for carrera, sinonimos in SINONIMOS_CARRERA:
        if any(re.search(rf"\b{re.escape(s)}\b", n) for s in sinonimos):
            return carrera
    return None


def solo_carrera(texto: str) -> bool:
    """True si el mensaje es casi solo el nombre de una carrera (respuesta a '¿de qué carrera eres?')."""
    n = normalizar(texto).strip(" .,!¿?")
    return normalizar_carrera(n) is not None and len(n.split()) <= 5


def extraer_perfil(texto: str) -> dict:
    """Datos de perfil que el estudiante declara de sí mismo (no se infieren de preguntas generales)."""
    datos = {}
    n = normalizar(texto)
    if _DECLARA_CARRERA.search(n) or solo_carrera(texto):
        carrera = normalizar_carrera(texto)
        if carrera:
            datos["carrera"] = carrera
    m = re.search(r"\bsede\s+([a-zñ ]{3,40}?)(?=[,.;:?!]| y | pero |$)", n)
    if m:
        datos["sede"] = m.group(1).strip().title()
    if "vespertin" in n:
        datos["jornada"] = "Vespertina"
    elif "diurn" in n:
        datos["jornada"] = "Diurna"
    return datos


def _num(s: str) -> float:
    return float(s.replace(",", "."))


def extraer_porcentaje(texto: str) -> Optional[float]:
    m = re.search(r"(\d{1,3}(?:[.,]\d+)?)\s*(%|por ?ciento)", normalizar(texto))
    if m and 0 <= _num(m.group(1)) <= 100:
        return _num(m.group(1))
    return None


def numero_suelto(texto: str) -> Optional[float]:
    """'72', 'llevo 72' o 'el 72%' como respuesta corta a una pregunta por un porcentaje."""
    m = re.fullmatch(r"\D{0,20}?(\d{1,3}(?:[.,]\d+)?)\s*(%|por ?ciento)?\D{0,20}", normalizar(texto).strip())
    if m and 0 <= _num(m.group(1)) <= 100:
        return _num(m.group(1))
    return None


_ASISTENCIA = (
    # "falté a 12 de 30 clases", "he faltado 12 veces de 30"
    re.compile(r"falt\w*\s+(?:a\s+)?(\d{1,3})\s+(?:clases?\s+|veces\s+)?de\s+(?:las?\s+|un total de\s+)?(\d{1,3})"),
    # "tengo 12 inasistencias de 30 clases"
    re.compile(r"(\d{1,3})\s+(?:inasistencias|faltas|ausencias)\s+de\s+(?:un total de\s+)?(\d{1,3})"),
)


def extraer_asistencia(texto: str) -> Optional[dict]:
    n = normalizar(texto)
    for patron in _ASISTENCIA:
        m = patron.search(n)
        if m:
            inasistencias, total = int(m.group(1)), int(m.group(2))
            if 0 < total and inasistencias <= total:
                tipo = "practica" if re.search(r"taller|laboratorio|practic", n) else "teorica"
                return {"clases_totales": total, "inasistencias": inasistencias, "tipo": tipo}
    return None


# "un 3,5 (30%)", "3.5 con 30%", "un 4,2 que vale 20%", "3,8 de 25%"
_NOTA = re.compile(r"\b([1-7](?:[.,]\d{1,2})?)\s*(?:\(|,)?\s*(?:con|que vale|que pesa|de|en una de|en)?\s*"
                   r"(?:un\s+)?(\d{1,3})\s*%")


def extraer_notas(texto: str) -> Optional[list]:
    notas = []
    for m in _NOTA.finditer(normalizar(texto)):
        nota, peso = _num(m.group(1)), float(m.group(2))
        if 1.0 <= nota <= 7.0 and 0 < peso <= 100:
            notas.append({"nota": nota, "ponderacion": peso})
    return notas or None
