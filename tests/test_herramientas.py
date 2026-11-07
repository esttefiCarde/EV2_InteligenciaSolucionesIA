"""Herramientas de consulta, razonamiento y escritura (sin red)."""
from datetime import date

import pytest

from src.herramientas import AGENTE_DE, AGENTES_EJECUTORES, REACTIVAS, Contexto, crear_herramientas
from src.memoria import MemoriaAgente
from tests.simulados import RagSimulado


@pytest.fixture
def ctx(tmp_path):
    return Contexto(usuario="ana", memoria=MemoriaAgente(":memory:"), consultar_rag=RagSimulado(),
                    fecha=lambda: date(2026, 11, 10), salidas=tmp_path)


def test_hay_herramientas_de_las_tres_categorias(ctx):
    h = crear_herramientas(ctx)
    assert set(AGENTES_EJECUTORES) == {"consulta", "razonamiento", "escritura"}
    assert all(nombre in h for nombre in AGENTE_DE)
    assert "redactar_solicitud" not in REACTIVAS and "olvidar_mis_datos" not in REACTIVAS
    # JSON Schema que lee el LLM en function calling
    assert h["calcular_asistencia"].args_schema.model_json_schema()["required"] == ["clases_totales", "inasistencias"]


def test_buscar_normativa_renumera_y_reutiliza_fuentes(ctx):
    h = crear_herramientas(ctx)
    r1 = h["calcular_asistencia"].invoke({"clases_totales": 30, "inasistencias": 3})
    r2 = h["buscar_normativa"].invoke({"pregunta": "¿Cuál es la asistencia mínima?"})
    r3 = h["buscar_normativa"].invoke({"pregunta": "¿Qué pasa si repruebo?"})
    assert r1["mensaje"].endswith("[1]") and "[1]" in r2["mensaje"]  # misma fuente (Art. 5) → mismo número
    assert "[2]" in r3["mensaje"] and len(ctx.fuentes) == 2


def test_buscar_normativa_sin_evidencia_y_sin_carrera(ctx):
    h = crear_herramientas(ctx)
    assert h["buscar_normativa"].invoke({"pregunta": "¿Cuánto vale el arancel?"})["sin_evidencia"]
    assert h["buscar_normativa"].invoke({"pregunta": "¿Qué necesito para la práctica?"})["falta"] == "carrera"
    ctx.perfil["carrera"] = "Contabilidad General"
    assert "fuentes" in h["buscar_normativa"].invoke({"pregunta": "¿Qué necesito para la práctica?"})


def test_verificar_requisitos_pide_lo_que_falta(ctx):
    h = crear_herramientas(ctx)
    assert h["verificar_requisitos_practica"].invoke({})["falta"] == "carrera"
    ctx.perfil["carrera"] = "Contabilidad General"
    assert h["verificar_requisitos_practica"].invoke({})["falta"] == "avance_malla"
    ctx.datos_turno["avance_malla"] = 72
    assert h["verificar_requisitos_practica"].invoke({})["cumple"] is True


def test_redactar_solicitud_sin_datos_personales(ctx):
    ctx.perfil["carrera"] = "Analista Programador"
    r = crear_herramientas(ctx)["redactar_solicitud"].invoke({"tipo": "inscripcion_practica",
                                                               "motivo": "mi RUT es 12.345.678-5"})
    texto = open(r["archivo"], encoding="utf-8").read()
    assert "Analista Programador" in texto and "[RUT]" in texto and "12.345.678" not in texto
    assert ctx.archivos == [r["archivo"]]


def test_derivacion_y_tramites_quedan_en_memoria(ctx):
    h = crear_herramientas(ctx)
    ticket = h["registrar_derivacion"].invoke({"area": "academico", "resumen": "caso con nota 3,4"})["ticket"]
    h["guardar_tramite"].invoke({"tramite": "practica", "etapa": "reunir_documentos"})
    r = h["consultar_mis_tramites"].invoke({})
    assert ticket in r["mensaje"] and "reunir documentos" in r["mensaje"]
    assert "3,4" not in ctx.memoria.tickets("ana")[0]["resumen"]  # minimización de datos


def test_falla_de_una_herramienta_se_informa(ctx):
    ctx.consultar_rag = RagSimulado(falla=1)
    r = crear_herramientas(ctx)["buscar_normativa"].invoke({"pregunta": "¿Con qué nota apruebo?"})
    assert r["error"].startswith("TimeoutError")
