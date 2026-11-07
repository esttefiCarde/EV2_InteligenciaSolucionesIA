import json
from src import router


def test_reglas_clasifica_areas():
    assert router.clasificar_por_palabras("Se me bloqueó la clave del AVA")[0] == "ti"
    assert router.clasificar_por_palabras("certificado de alumno regular")[0] == "administrativo"
    assert router.clasificar_por_palabras("requisitos de la práctica")[0] == "practica_titulacion"
    assert router.clasificar_por_palabras("repruebo el ramo")[0] == "academico"


def test_reglas_sin_coincidencia_es_otro():
    assert router.clasificar_por_palabras("receta de cocina") == ("otro", 0.0)


def test_parsear_json_con_texto_extra():
    salida = 'Claro:\n```json\n{"area": "ti", "confianza": 0.9, "carrera": null, "motivo": "x"}\n```'
    r = router.parsear_router(salida)
    assert r["area"] == "ti" and r["confianza"] == 0.9


def test_parsear_area_invalida():
    assert router.parsear_router('{"area": "deportes", "confianza": 1}') is None
    assert router.parsear_router("no es json") is None


def test_clasificar_usa_llm():
    gen = lambda s, u: json.dumps({"area": "administrativo", "confianza": 0.9, "carrera": None, "motivo": ""})
    assert router.clasificar("lo que sea", gen)["area"] == "administrativo"


def test_clasificar_respaldo_si_llm_falla():
    def gen(s, u):
        raise TimeoutError("sin red")
    r = router.clasificar("se bloqueó mi clave", gen)
    assert r["area"] == "ti" and "respaldo" in r["motivo"]


def test_baja_confianza_llm_usa_regla_fuerte():
    gen = lambda s, u: json.dumps({"area": "academico", "confianza": 0.2, "carrera": None, "motivo": ""})
    r = router.clasificar("no puedo ingresar a la intranet, clave bloqueada", gen)
    assert r["area"] == "ti"
