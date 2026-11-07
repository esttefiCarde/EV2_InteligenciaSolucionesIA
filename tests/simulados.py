"""Dobles de prueba: RAG del EP1 y modelos de chat simulados (sin red ni modelos descargados)."""
from typing import Any, Optional

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel

from src.guardrails import normalizar
from src.modelos import Respuesta

_DOCS = [  # (claves, área, fuente, texto)
    (("arancel", "cuota", "valor de"), None, None, None),  # sin evidencia
    (("hora", "dura"), "practica_titulacion", "Manual de Práctica Profesional (simulado) – 2. Requisitos específicos por carrera",
     "La duración depende de tu carrera: por ejemplo, 360 horas en Ingeniería en Informática [1]."),
    (("practica",), "practica_titulacion", "Manual de Práctica Profesional (simulado) – 3. Documentos necesarios",
     "Necesitas la carta de presentación, la ficha de inscripción, el seguro y la carta de aceptación [1]."),
    (("titul",), "practica_titulacion", "Guía de Titulación (simulada) – 2. Documentos para iniciar el proceso",
     "Debes presentar el formulario de inscripción y los certificados de práctica y de notas [1]."),
    (("repruebo", "reprob"), "academico", "Reglamento Académico (simulado) – Art. 8. Reprobación de asignaturas",
     "Debes cursarla de nuevo; a la tercera reprobación hay causal de eliminación [1]."),
    (("asistencia",), "academico", "Reglamento Académico (simulado) – Art. 5. Asistencia",
     "La asistencia mínima es 60 % en teóricas y 70 % en talleres [1]."),
    (("nota", "apruebo"), "academico", "Reglamento Académico (simulado) – Art. 4. Escala de notas y aprobación",
     "Se aprueba con nota 4,0 [1]."),
    (("suspen", "retir"), "administrativo", "Guía de Trámites y Certificados (simulada) – 4. Retiro de asignaturas y suspensión",
     "Se solicita por escrito en el Punto Estudiantil dentro del período del calendario [1]."),
    (("justific", "inasistencia"), "academico", "Reglamento Académico (simulado) – Art. 6. Inasistencias a evaluaciones",
     "Justificas ante tu coordinación con un certificado médico u otro antecedente [1]."),
    (("certificado",), "administrativo", "Guía de Trámites y Certificados (simulada) – 1. Certificado de alumno regular",
     "Se pide en la Intranet, menú Trámites > Certificados [1]."),
]


class RagSimulado:
    """Imita AsistenteDuoc.consultar(pregunta, carrera, area) y registra las llamadas."""

    def __init__(self, falla: int = 0):
        self.llamadas = []
        self.falla = falla  # cuántas llamadas iniciales lanzan una excepción

    def __call__(self, pregunta: str, carrera: Optional[str] = None, area: Optional[str] = None) -> Respuesta:
        self.llamadas.append({"pregunta": pregunta, "carrera": carrera, "area": area})
        if self.falla:
            self.falla -= 1
            raise TimeoutError("servicio no disponible")
        n = normalizar(pregunta)
        for claves, area_doc, fuente, texto in _DOCS:
            if any(c in n for c in claves):
                if fuente is None:
                    return Respuesta(texto="No encontré esta información.", area="administrativo", derivado=True,
                                     motivo_derivacion="sin_informacion")
                if area_doc == "practica_titulacion" and "practica" in n and not carrera and "hora" not in n:
                    return Respuesta(texto="¿De qué carrera eres?", area=area_doc, pide_aclaracion=True)
                return Respuesta(texto=texto, area=area_doc, fuentes=[f"[1] {fuente} (interno, v2026.1)"])
        return Respuesta(texto="No encontré documentos relacionados.", area="otro", derivado=True,
                         motivo_derivacion="fuera_de_alcance")


class ChatConHerramientas(FakeMessagesListChatModel):
    """Modelo de chat simulado que acepta bind_tools y with_structured_output."""
    plan: Any = None

    def bind_tools(self, tools, **kwargs):
        return self

    def with_structured_output(self, schema, **kwargs):
        from langchain_core.runnables import RunnableLambda
        return RunnableLambda(lambda _: self.plan)
