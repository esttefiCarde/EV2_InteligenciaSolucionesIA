"""Interfaz de consola del agente (EP2).

Uso:
    python -m src.cli                                   conversación (comandos: /traza, /memoria, /nueva, salir)
    python -m src.cli --usuario ana "Quiero empezar mi práctica"     un solo mensaje
    python -m src.cli --fecha 2026-12-05 "..."          fecha simulada del calendario (condiciones cambiantes)
    python -m src.cli --ep1 "¿Con qué nota apruebo?"    pipeline RAG del EP1, sin agente
"""
import argparse
import sys
import uuid
from datetime import date

ICONOS = {"pensamiento": "💭", "accion": "🛠️ ", "observacion": "👁️ ", "decision": "🧭", "memoria": "🧠",
          "guardrail": "🛡️ "}


def imprimir(r, traza: bool) -> None:
    print(f"\n[estrategia: {r.estrategia} · plan: {r.metodo_plan or '-'} · herramientas: {len(r.herramientas)} · "
          f"replanificaciones: {r.replanes} · llamadas LLM: {r.llamadas_llm} · {r.latencia_ms} ms]")
    if traza:
        for t in r.traza:
            print(f"  {ICONOS.get(t['tipo'], '·')} {t['texto']}")
    print(f"\nAsistente: {r.texto}")
    if r.fuentes:
        print("\nFuentes:\n" + "\n".join(r.fuentes))
    for archivo in r.archivos:
        print(f"\n📝 Borrador guardado en: {archivo}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mensaje", nargs="*")
    ap.add_argument("--usuario", default="estudiante_cli", help="alias del estudiante (no uses tu nombre ni RUT)")
    ap.add_argument("--sesion", default=None)
    ap.add_argument("--fecha", type=date.fromisoformat, default=None, help="AAAA-MM-DD para el calendario")
    ap.add_argument("--sin-traza", action="store_true")
    ap.add_argument("--ep1", action="store_true", help="usa el pipeline RAG del EP1 sin agente")
    a = ap.parse_args()

    if a.ep1:
        from .pipeline import formatear
        from .retrieval import crear_asistente
        r = crear_asistente().consultar(" ".join(a.mensaje))
        print(f"[área: {r.area} | derivado: {r.derivado}]\n{formatear(r)}")
        return

    from .agente import crear_agente
    agente = crear_agente()
    sesion, traza = a.sesion or uuid.uuid4().hex[:8], not a.sin_traza
    if a.mensaje:
        imprimir(agente.conversar(" ".join(a.mensaje), a.usuario, sesion, a.fecha), traza)
        return
    print(f"Asistente Duoc UC · agente EP2 (usuario: {a.usuario}, sesión: {sesion}). "
          "Comandos: /traza, /memoria, /nueva, salir")
    while True:
        try:
            m = input("\nTú: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if m.lower() in {"salir", "exit", "q"}:
            break
        if m == "/traza":
            traza = not traza
            print(f"Traza {'activada' if traza else 'desactivada'}")
        elif m == "/memoria":
            mem = agente.memoria
            print(f"Perfil: {mem.perfil(a.usuario)}\nTrámites: {mem.tramites(a.usuario)}\n"
                  f"Tickets: {mem.tickets(a.usuario)}\nVentana de corto plazo: "
                  f"{len(mem.ventana(a.usuario, sesion))} mensajes (k={mem.k} turnos)")
        elif m == "/nueva":
            sesion = uuid.uuid4().hex[:8]
            print(f"Nueva sesión {sesion}: la memoria de corto plazo parte vacía; la de largo plazo se mantiene.")
        elif m:
            imprimir(agente.conversar(m, a.usuario, sesion, a.fecha), traza)


if __name__ == "__main__":
    main()
