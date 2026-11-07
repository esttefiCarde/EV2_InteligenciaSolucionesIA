"""Evalúa el asistente con evaluacion/preguntas_prueba.json y genera evidencia.

Uso:
    python scripts/evaluar.py                 # sistema completo (requiere .env y base indexada)
    python scripts/evaluar.py --solo-router   # solo clasificador por reglas (sin red ni LLM)

Métricas: precisión del enrutamiento, acierto de recuperación (documento esperado entre las
fuentes), acierto de derivación/aclaración, citas en respuestas no derivadas y latencia media.
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import router  # noqa: E402


def cargar_casos():
    return json.loads((ROOT / "evaluacion" / "preguntas_prueba.json").read_text(encoding="utf-8"))


def evaluar_router_reglas(casos):
    aciertos = 0
    for c in casos:
        area, _ = router.clasificar_por_palabras(c["pregunta"])
        aciertos += area == c["area"]
    return {"modo": "solo_router_reglas", "n": len(casos), "precision_router": aciertos / len(casos)}


def evaluar_completo(casos):
    from src.retrieval import crear_asistente
    asistente = crear_asistente()
    filas, lat = [], []
    for c in casos:
        t0 = time.time()
        r = asistente.consultar(c["pregunta"])
        lat.append((time.time() - t0) * 1000)
        esperado = c["derivar"]
        if esperado == "aclaracion":
            ok_deriv = r.pide_aclaracion
        else:
            ok_deriv = (r.derivado == esperado) and not r.pide_aclaracion
        docs = {f.doc_id for f in r.fragmentos}
        ok_doc = None if c["doc"] is None else (c["doc"] in docs)
        con_cita = None if (r.derivado or r.pide_aclaracion) else bool(r.fuentes)
        filas.append({"id": c["id"], "area_real": r.area, "area_esperada": c["area"],
                      "ok_area": r.area == c["area"], "ok_derivacion": ok_deriv, "ok_doc": ok_doc,
                      "con_cita": con_cita, "motivo": r.motivo_derivacion, "reruteado": r.reruteado})

    def pct(campo, universo=lambda f: True):
        v = [f[campo] for f in filas if universo(f) and f[campo] is not None]
        return round(sum(v) / len(v), 3) if v else None

    return {"modo": "completo", "n": len(casos), "precision_enrutamiento": pct("ok_area"),
            "acierto_derivacion": pct("ok_derivacion"), "acierto_recuperacion": pct("ok_doc"),
            "tasa_citas": pct("con_cita"), "latencia_media_ms": round(statistics.mean(lat)),
            "detalle": filas}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo-router", action="store_true")
    a = ap.parse_args()
    casos = cargar_casos()
    res = evaluar_router_reglas(casos) if a.solo_router else evaluar_completo(casos)
    salida = ROOT / "evaluacion" / f"resultados_{res['modo']}.json"
    salida.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "detalle"}, indent=2, ensure_ascii=False))
    print(f"Detalle guardado en {salida.relative_to(ROOT)}")
