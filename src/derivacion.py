"""Agente de derivación: decide cuándo NO responder y arma el traspaso a una persona."""
from .config import CONTACTOS

MOTIVOS = {
    "sin_informacion": "No encontré esta información en los documentos oficiales disponibles.",
    "caso_excepcional": "Tu situación combina varios factores y requiere revisión personalizada.",
    "sensible": "Tu consulta es delicada y es mejor que la atienda una persona.",
    "baja_relevancia": "No encontré documentos suficientemente relacionados con tu consulta.",
    "fuera_de_alcance": "Esta consulta está fuera de lo que puedo responder.",
    "inyeccion": "No puedo procesar esa solicitud.",
    "error_servicio": "Tuve un problema técnico al generar la respuesta.",
}


def construir_mensaje(motivo: str, area: str, pregunta_enmascarada: str) -> str:
    contacto = CONTACTOS.get(area, CONTACTOS["otro"])
    cabecera = MOTIVOS.get(motivo, MOTIVOS["sin_informacion"])
    if motivo == "inyeccion":
        return ("No puedo procesar esa solicitud. Puedo ayudarte con dudas académicas, "
                "administrativas, de práctica/titulación o de plataformas de Duoc UC.")
    if motivo == "sensible":
        return (f"{cabecera} Te recomiendo contactar a {contacto} o a la unidad de apoyo "
                "estudiantil de tu sede. Si sientes que estás en riesgo, comunícate de inmediato "
                "con una persona de confianza o con los servicios de emergencia.")
    return (f"{cabecera} Para no darte información incorrecta, te sugiero consultar a {contacto}.\n\n"
            f"Puedes copiar este resumen en tu solicitud (sin datos personales):\n"
            f"\"{pregunta_enmascarada}\"")


def evaluar_confianza(fragmentos: list, umbral: float) -> bool:
    """True si hay evidencia suficiente para responder."""
    return bool(fragmentos) and max(f.score for f in fragmentos) >= umbral
