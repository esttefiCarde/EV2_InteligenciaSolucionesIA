"""Generador local (sin token): no debe responder con un fragmento que no contesta la pregunta."""
from src.llm import _generador_fallback
from src.modelos import Fragmento
from src.pipeline import AsistenteDuoc

ART9 = Fragmento(texto="## Art. 9. Examen final\nLos estudiantes con nota de presentación igual o superior a 4,0 "
                       "pueden rendir el examen final.", doc_id="reg", fuente="Reglamento", seccion="Art. 9",
                 area="academico", score=0.57)
ART5 = Fragmento(texto="## Art. 5. Asistencia\nLa asistencia mínima para aprobar una asignatura teórica es 60 %.",
                 doc_id="reg", fuente="Reglamento", seccion="Art. 5", area="academico", score=0.45)


def asistente(*fragmentos):
    return AsistenteDuoc(_generador_fallback, lambda q, area: list(fragmentos), registrar=False)


def test_fragmento_parecido_pero_sin_la_respuesta_deriva():
    r = asistente(ART9).consultar("¿Cuál es el último día de clases del semestre?")
    assert r.derivado and r.motivo_derivacion == "sin_informacion" and not r.fuentes


def test_elige_el_fragmento_que_contiene_la_respuesta():
    r = asistente(ART9, ART5).consultar("¿Cuál es la asistencia mínima para aprobar?")
    assert not r.derivado and "Art. 5" in r.fuentes[0] and "60 %" in r.texto


def test_reconoce_como_escribe_el_estudiante():
    art4 = Fragmento(texto="## Art. 4. Escala de notas y aprobación\nLa nota mínima de aprobación de una asignatura "
                           "es 4,0.", doc_id="reg", fuente="Reglamento", seccion="Art. 4", area="academico", score=0.5)
    r = asistente(art4).consultar("¿Con qué nota apruebo un ramo?")
    assert not r.derivado and "4,0" in r.texto


def test_sin_contexto_o_sin_pregunta_responde_sin_informacion():
    assert _generador_fallback("system", "sin fragmentos") == "SIN_INFORMACION"
