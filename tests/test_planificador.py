"""Estrategia, planificación (reglas y LLM) y política de decisión del Manager."""
import pytest

from src import planificador as pl
from src.herramientas import Contexto, crear_herramientas
from src.memoria import MemoriaAgente
from tests.simulados import RagSimulado


@pytest.fixture
def herramientas():
    return crear_herramientas(Contexto(usuario="t", memoria=MemoriaAgente(":memory:"), consultar_rag=RagSimulado()))


@pytest.mark.parametrize("consulta,intencion,estrategia", [
    ("Quiero empezar mi práctica, ¿cumplo?", "practica", "planificada"),
    ("¿Qué necesito para la práctica?", "consulta", "reactiva"),
    ("Falté a 12 de 30 clases", "asistencia", "reactiva"),
    ("¿En qué quedé con mi titulación?", "seguimiento", "planificada"),
    ("Repetí un ramo tres veces y tuve un problema de salud", "excepcional", "directa"),
    ("Borra mis datos", "olvidar", "directa"),
    ("Soy de Contabilidad General", "consulta", "reactiva"),  # 'General' no es pedir un documento
])
def test_intencion_y_estrategia(consulta, intencion, estrategia):
    assert pl.detectar_intencion(consulta) == intencion
    assert pl.elegir_estrategia(intencion)[0] == estrategia


def test_plan_de_practica_por_reglas():
    pasos = pl.planificar_por_reglas("Quiero inscribir mi práctica, prepárame la solicitud", "practica")
    assert [p["herramienta"] for p in pasos] == ["verificar_requisitos_practica", "buscar_normativa",
                                                 "consultar_calendario", "redactar_solicitud", "guardar_tramite"]
    assert [p["agente"] for p in pasos] == ["razonamiento", "consulta", "consulta", "escritura", "escritura"]


def test_validar_plan_del_llm(herramientas):
    plan = pl.PlanLLM(objetivo="x", pasos=[
        pl.PasoLLM(herramienta="hackear", objetivo="?"),
        pl.PasoLLM(herramienta="olvidar_mis_datos", objetivo="?"),
        pl.PasoLLM(herramienta="calcular_asistencia", objetivo="?", argumentos={"clases_totales": "muchas"}),
        pl.PasoLLM(herramienta="buscar_normativa", objetivo="requisitos", argumentos={"pregunta": "¿Requisitos?"}),
        pl.PasoLLM(herramienta="redactar_solicitud", objetivo="borrador", argumentos={"tipo": "inscripcion_practica"}),
    ])
    pasos, notas = pl.validar_plan(plan, herramientas, "Quiero empezar mi práctica", "practica")
    assert [p["herramienta"] for p in pasos] == ["buscar_normativa", "guardar_tramite"]
    assert len(notas) == 5  # 4 descartes + guardar_tramite agregado por el Manager


def test_si_el_llm_falla_se_usa_el_plan_por_reglas(herramientas):
    def llm_caido(consulta, contexto):
        raise ConnectionError("sin red")
    r = pl.planificar("Quiero iniciar mi titulación", "titulacion", {}, herramientas, llm_caido)
    assert r["metodo"].startswith("reglas (el LLM falló") and r["pasos"][0]["herramienta"] == "buscar_normativa"


def test_acciones_criticas_nunca_se_delegan_al_llm(herramientas):
    def llm(consulta, contexto):
        raise AssertionError("no debe llamarse")
    assert pl.planificar("Borra mis datos", "olvidar", {}, herramientas, llm)["metodo"] == "reglas"


def _plan(*herramientas, **args):
    return [pl.paso(h, "t", **args.get(h, {})) for h in herramientas]


def test_falta_un_dato_pausa_el_plan():
    d = pl.evaluar_paso(_plan("verificar_requisitos_practica", "buscar_normativa"), 0, {"falta": "carrera"}, 1, 0, 1, "q")
    assert d["accion"] == "pedir_dato" and d["falta"] == "carrera" and d["siguiente"] == 0


def test_no_cumple_requisitos_replanifica():
    plan = _plan("verificar_requisitos_practica", "buscar_normativa", "consultar_calendario", "redactar_solicitud",
                 "guardar_tramite", guardar_tramite={"tramite": "practica", "etapa": "entregar_solicitud"})
    d = pl.evaluar_paso(plan, 0, {"cumple": False, "avance_minimo": 80}, 1, 0, 1, "q")
    estados = {p["herramienta"]: p["estado"] for p in d["plan"]}
    assert d["replan"] and estados["consultar_calendario"] == estados["redactar_solicitud"] == "omitido"
    assert d["plan"][-1]["args"]["etapa"] == "cumplir_requisitos" and d["siguiente"] == 1


def test_periodo_cerrado_no_redacta():
    plan = _plan("consultar_calendario", "redactar_solicitud", "guardar_tramite",
                 guardar_tramite={"tramite": "practica", "etapa": "entregar_solicitud"})
    r = {"estado": "cerrado", "evento": "inscripcion_practica", "inicio": "2026-11-02"}
    d = pl.evaluar_paso(plan, 0, r, 1, 0, 1, "q")
    assert d["plan"][1]["estado"] == "omitido" and d["plan"][2]["args"]["etapa"] == "esperar_apertura"


def test_sin_evidencia_agrega_derivacion():
    d = pl.evaluar_paso(_plan("buscar_normativa", "redactar_solicitud"), 0, {"sin_evidencia": True, "area": "ti"},
                        1, 0, 1, "q")
    assert [p["herramienta"] for p in d["plan"]] == ["buscar_normativa", "registrar_derivacion", "redactar_solicitud"]
    assert d["plan"][1]["args"]["area"] == "ti" and d["plan"][2]["estado"] == "omitido"


def test_riesgo_de_reprobar_agrega_un_paso_al_final():
    d = pl.evaluar_paso(_plan("calcular_asistencia", "buscar_normativa"), 0, {"cumple": False}, 1, 0, 1, "q")
    assert d["plan"][-1]["agregado"] and "repruebo" in d["plan"][-1]["args"]["pregunta"]


def test_falla_reintenta_y_luego_deriva():
    plan = _plan("buscar_normativa", "consultar_calendario")
    d1 = pl.evaluar_paso(plan, 0, {"error": "Timeout"}, 1, 0, 1, "q")
    assert d1["accion"] == "reintentar" and d1["siguiente"] == 0
    d2 = pl.evaluar_paso(d1["plan"], 0, {"error": "Timeout"}, 2, 0, 2, "q")
    assert d2["replan"] and d2["plan"][1]["herramienta"] == "registrar_derivacion"
    assert d2["plan"][2]["estado"] == "omitido"


def test_limites_de_iteraciones_y_replanes():
    plan = _plan("calcular_asistencia", "buscar_normativa")
    assert pl.evaluar_paso(plan, 0, {"cumple": False}, 1, pl.MAX_REPLANES, 1, "q")["replan"] is False
    assert pl.evaluar_paso(plan, 0, {"mensaje": "ok"}, 1, 0, pl.MAX_ITERACIONES, "q")["accion"] == "finalizar"
