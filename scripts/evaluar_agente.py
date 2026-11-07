"""Evalúa el agente con escenarios multi-turno (evaluacion/escenarios_agente.json) y genera evidencia.

Uso:
    python scripts/evaluar_agente.py              # sistema real: índice ChromaDB + LLM si hay GITHUB_TOKEN
    python scripts/evaluar_agente.py --simulado   # RAG simulado y sin LLM (reproducible y sin red)

Cada escenario usa un estudiante nuevo y una memoria temporal (no toca memoria/agente.db).
Métricas por turno: estrategia, herramientas, replanificación, pausa, derivación, etapa guardada en la
memoria de largo plazo, contenido de la respuesta, latencia y llamadas al LLM.
Con token, la corrida completa usa unas 60 llamadas a GitHub Models (revisa tu cuota diaria).
"""
import argparse
import json
import statistics
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CRITERIOS = ("estrategia", "herramientas", "replan", "esperando", "derivado", "etapa", "texto", "con_fuentes",
             "archivos", "decision", "memoria_vacia")


def crear(simulado: bool, salidas: Path):
    if simulado:
        from src.agente import AgenteDuoc
        from src.memoria import MemoriaAgente
        from tests.simulados import RagSimulado
        return AgenteDuoc(rag=RagSimulado(), memoria=MemoriaAgente(":memory:"), salidas=salidas, registrar=False)
    from src.agente import crear_agente
    return crear_agente(memoria_db=":memory:", dir_vectorial=None, salidas=salidas, registrar=False)


def verificar(esperado: dict, r, agente, usuario: str) -> dict:
    ok = {}
    for k, v in esperado.items():
        if k == "estrategia":
            ok[k] = r.estrategia == v
        elif k == "herramientas":
            ok[k] = all(h in r.herramientas for h in v)
        elif k == "replan":
            ok[k] = (r.replanes > 0) == v
        elif k == "esperando":
            ok[k] = r.esperando == v
        elif k == "derivado":
            ok[k] = r.derivado == v
        elif k == "etapa":
            ok[k] = any(t["etapa"] == v for t in agente.memoria.tramites(usuario))
        elif k == "texto":
            ok[k] = all(t.lower() in r.texto.lower() for t in v)
        elif k == "con_fuentes":
            ok[k] = bool(r.fuentes) == v
        elif k == "archivos":
            ok[k] = len(r.archivos) == v
        elif k == "decision":
            ok[k] = any(v in t["texto"] for t in r.traza if t["tipo"] == "decision")
        elif k == "memoria_vacia":
            ok[k] = not agente.memoria.perfil(usuario) and not agente.memoria.tramites(usuario)
    return ok


def transcribir(esc: dict, filas: list) -> str:
    md = [f"## {esc['id']} · {esc['nombre']}", f"*Condición:* {esc['condicion']} · *fecha del calendario:* {esc['fecha']}", ""]
    for f in filas:
        estado = "✅" if all(f["checks"].values()) else "❌ " + ", ".join(k for k, v in f["checks"].items() if not v)
        md += [f"**Estudiante (sesión {f['sesion']}):** {f['mensaje']}", "",
               f"*Estrategia:* {f['estrategia']} · *plan:* {f['metodo_plan']} · *herramientas:* "
               f"{' → '.join(f['herramientas']) or '—'} · *replanificaciones:* {f['replanes']} · "
               f"*llamadas LLM:* {f['llamadas_llm']} · *verificación:* {estado}", "",
               "<details><summary>Traza del agente</summary>", ""]
        md += [f"- **{t['tipo']}**: {t['texto']}" for t in f["traza"]]
        md += ["", "</details>", "", "**Asistente:**", "", "> " + f["respuesta"].replace("\n", "\n> "), ""]
        if f["fuentes"]:
            md += ["Fuentes: " + "; ".join(f["fuentes"]), ""]
    return "\n".join(md)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--simulado", action="store_true")
    a = ap.parse_args()
    escenarios = json.loads((ROOT / "evaluacion" / "escenarios_agente.json").read_text(encoding="utf-8"))

    from src.llm import hay_token
    modo = "simulado" if a.simulado else ("real_llm" if hay_token() else "real_local")
    with tempfile.TemporaryDirectory() as tmp:
        agente = crear(a.simulado, Path(tmp))
        detalle, md, lat, llamadas = [], [], [], []
        for esc in escenarios:
            usuario, filas = f"eval_{esc['id']}", []
            for t in esc["turnos"]:
                r = agente.conversar(t["mensaje"], usuario, f"{esc['id']}-{t['sesion']}", date.fromisoformat(esc["fecha"]))
                lat.append(r.latencia_ms)
                llamadas.append(r.llamadas_llm)
                filas.append({"sesion": t["sesion"], "mensaje": t["mensaje"], "estrategia": r.estrategia,
                              "metodo_plan": r.metodo_plan, "herramientas": r.herramientas, "replanes": r.replanes,
                              "esperando": r.esperando, "derivado": r.derivado, "llamadas_llm": r.llamadas_llm,
                              "latencia_ms": r.latencia_ms, "respuesta": r.texto, "fuentes": r.fuentes,
                              "traza": r.traza, "checks": verificar(t["esperado"], r, agente, usuario)})
            ok = all(all(f["checks"].values()) for f in filas)
            print(f"{esc['id']} {'✅' if ok else '❌'} {esc['nombre']}")
            detalle.append({"id": esc["id"], "nombre": esc["nombre"], "condicion": esc["condicion"], "ok": ok,
                            "turnos": [{k: v for k, v in f.items() if k != "traza"} for f in filas]})
            md.append(transcribir(esc, filas))

    turnos = [f for e in detalle for f in e["turnos"]]
    por_criterio = {}
    for c in CRITERIOS:
        v = [f["checks"][c] for f in turnos if c in f["checks"]]
        if v:
            por_criterio[c] = f"{sum(v)}/{len(v)}"
    res = {"modo": modo, "fecha_ejecucion": date.today().isoformat(), "escenarios": len(detalle),
           "escenarios_ok": sum(e["ok"] for e in detalle), "turnos": len(turnos),
           "turnos_ok": sum(all(f["checks"].values()) for f in turnos), "por_criterio": por_criterio,
           "estrategias": {e: sum(f["estrategia"] == e for f in turnos) for e in ("reactiva", "planificada", "directa")},
           "replanificaciones": sum(f["replanes"] for f in turnos), "latencia_media_ms": round(statistics.mean(lat)),
           "llamadas_llm_por_turno": round(statistics.mean(llamadas), 2), "detalle": detalle}
    (ROOT / "evaluacion" / f"resultados_agente_{modo}.json").write_text(
        json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    (ROOT / "evidencia").mkdir(exist_ok=True)
    cabecera = (f"# Transcripción de escenarios del agente ({modo})\n\nGenerado con `python scripts/evaluar_agente.py"
                f"{' --simulado' if a.simulado else ''}` el {res['fecha_ejecucion']}. Escenarios correctos: "
                f"{res['escenarios_ok']}/{res['escenarios']} · turnos correctos: {res['turnos_ok']}/{res['turnos']}.\n\n")
    (ROOT / "evidencia" / f"transcripcion_agente_{modo}.md").write_text(cabecera + "\n\n".join(md), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "detalle"}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
