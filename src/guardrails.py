"""Controles de seguridad previos y posteriores al LLM (lógica determinista).

- Privacidad (Ley 19.628): se detecta y enmascara el RUT antes de enviar a un LLM o guardar logs.
- Casos excepcionales / sensibles: se derivan a una persona sin intentar resolverlos.
- Prompt injection básico.
- Variaciones por carrera: si el tema cambia según carrera y no se conoce, se pide aclarar.
"""
import re
import unicodedata


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes para comparar palabras clave."""
    t = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


# --- Privacidad -----------------------------------------------------------
_RUT = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dkK]\b")
_CORREO = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_FRASES_NOTAS = ("mis notas", "mi promedio", "mi nota ", "mi situacion academica")


def detectar_datos_sensibles(texto: str) -> list:
    tipos = []
    if _RUT.search(texto):
        tipos.append("RUT")
    if _CORREO.search(texto):
        tipos.append("correo")
    n = normalizar(texto)
    if any(f in n for f in _FRASES_NOTAS):
        tipos.append("situacion_academica")
    return tipos


def enmascarar(texto: str) -> str:
    texto = _RUT.sub("[RUT]", texto)
    return _CORREO.sub("[CORREO]", texto)


# --- Prompt injection -----------------------------------------------------
_INYECCION = (
    "ignora las instrucciones", "ignora todo lo anterior", "olvida tus instrucciones",
    "ignore previous", "ignore all previous", "system prompt", "prompt del sistema",
    "actua como", "eres ahora", "muestrame tus instrucciones", "modo desarrollador",
)


def detectar_inyeccion(texto: str) -> bool:
    n = normalizar(texto)
    return any(p in n for p in _INYECCION)


# --- Casos sensibles o excepcionales -------------------------------------
_SENSIBLES = (
    "acoso", "abuso", "violencia", "discriminacion", "denuncia", "suicid",
    "hacerme dano", "autolesion", "me quiero morir", "amenaza",
)
_FACTORES = {
    "reprobacion": ("repeti", "repruebo", "reprobe", "reprobar", "reprobado", "reprobacion"),
    "salud": ("salud", "enfermedad", "hospital", "depresion", "licencia", "operacion"),
    "economico": ("economic", "no puedo pagar", "deuda", "arancel", "trabajo y estudio"),
    "familiar": ("familiar", "fallecio", "duelo", "embarazo", "cuidado de"),
    "apelacion": ("apelar", "apelacion", "reclamo", "reconsiderar"),
}


def es_caso_sensible(texto: str) -> bool:
    n = normalizar(texto)
    return any(p in n for p in _SENSIBLES)


def contar_factores(texto: str) -> list:
    n = normalizar(texto)
    return [f for f, claves in _FACTORES.items() if any(c in n for c in claves)]


def es_caso_excepcional(texto: str) -> bool:
    """Caso particular: combina 2+ factores (p. ej. reprobación + salud) o pide apelar."""
    factores = contar_factores(texto)
    return len(factores) >= 2 or "apelacion" in factores


# --- Variaciones por carrera ---------------------------------------------
_TEMAS_VARIABLES = ("practica", "titulacion", "titularme", "titulo", "convalid", "malla")


def requiere_carrera(texto: str, carrera: str | None) -> bool:
    """True si el tema cambia entre carreras y aún no se conoce la del estudiante."""
    if carrera and carrera.strip():
        return False
    n = normalizar(texto)
    return any(t in n for t in _TEMAS_VARIABLES)
