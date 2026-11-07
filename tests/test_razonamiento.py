"""Extracción de datos y cálculos deterministas que usan las herramientas de razonamiento."""
from datetime import date

from src import razonamiento as rz
from src.extraccion import (extraer_asistencia, extraer_notas, extraer_perfil, extraer_porcentaje,
                            normalizar_carrera, numero_suelto)


def test_normalizar_carrera_con_sinonimos():
    assert normalizar_carrera("soy de informática") == "Ingeniería en Informática"
    assert normalizar_carrera("estudio Contabilidad") == "Contabilidad General"
    assert normalizar_carrera("Analista Programador") == "Analista Programador"
    assert normalizar_carrera("me gusta el fútbol") is None


def test_perfil_solo_si_el_estudiante_lo_declara():
    assert extraer_perfil("Soy de Enfermería, sede Maipú") == {"carrera": "Enfermería", "sede": "Maipu"}
    assert extraer_perfil("¿Cuántas horas dura la práctica de Informática?") == {}
    assert extraer_perfil("Contabilidad General") == {"carrera": "Contabilidad General"}


def test_porcentajes_y_respuestas_cortas():
    assert extraer_porcentaje("llevo 72% de la malla") == 72
    assert extraer_porcentaje("llevo 72,5 por ciento") == 72.5
    assert numero_suelto("llevo 72") == 72
    assert numero_suelto("el 85%") == 85
    assert numero_suelto("no sé cuánto llevo") is None


def test_extraer_asistencia_y_notas():
    assert extraer_asistencia("En el taller falté a 12 de 30 clases") == \
        {"clases_totales": 30, "inasistencias": 12, "tipo": "practica"}
    assert extraer_asistencia("tengo 5 inasistencias de 40 clases")["tipo"] == "teorica"
    assert extraer_notas("Tengo un 3,5 (30%) y un 4,2 (20%)") == \
        [{"nota": 3.5, "ponderacion": 30}, {"nota": 4.2, "ponderacion": 20}]


def test_requisitos_practica_segun_carrera():
    assert rz.evaluar_requisitos_practica("Contabilidad General", 72)["cumple"] is True
    r = rz.evaluar_requisitos_practica("Ingeniería en Informática", 72)
    assert r["cumple"] is False and "8 puntos" in r["mensaje"]
    assert rz.evaluar_requisitos_practica("Enfermería", 0)["gestion_individual"] is False


def test_asistencia_teorica_y_practica():
    r = rz.calcular_asistencia(30, 12, "practica")
    assert r["asistencia"] == 60 and r["minimo"] == 70 and r["cumple"] is False
    r = rz.calcular_asistencia(30, 12, "teorica")
    assert r["cumple"] is True and r["faltas_restantes"] == 0


def test_nota_necesaria():
    r = rz.calcular_nota_necesaria([{"nota": 3.5, "ponderacion": 30}, {"nota": 4.0, "ponderacion": 20}])
    assert r["alcanzable"] is True and r["nota_necesaria"] == 4.3
    r = rz.calcular_nota_necesaria([{"nota": 1.0, "ponderacion": 70}])
    assert r["alcanzable"] is False


def test_estado_del_periodo_segun_la_fecha():
    assert rz.estado_periodo("inscripcion_practica", date(2026, 11, 10))["estado"] == "abierto"
    assert rz.estado_periodo("inscripcion_practica", date(2026, 12, 5))["estado"] == "cerrado"
    assert rz.estado_periodo("inscripcion_titulacion", date(2026, 11, 10))["estado"] == "proximo"
