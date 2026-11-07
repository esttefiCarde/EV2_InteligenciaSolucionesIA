"""Interfaz web (Streamlit) del agente EP2: chat + panel de razonamiento, plan y memoria."""
import uuid
from dataclasses import asdict
from pathlib import Path

import streamlit as st

from src import razonamiento as rz
from src.agente import crear_agente
from src.config import LLM_MODEL, LLM_MODEL_MANAGER
from src.herramientas import AGENTES_EJECUTORES, NOMBRE_TRAMITE, etapa_legible
from src.llm import hay_token

st.set_page_config(page_title="Asistente Duoc UC · Agente", page_icon="🎓", layout="wide")
ICONOS = {"pensamiento": "💭", "accion": "🛠️", "observacion": "👁️", "decision": "🧭", "memoria": "🧠",
          "guardrail": "🛡️"}
ESTADO_PASO = {"ok": "✅", "omitido": "⏭️", "pendiente": "⏸️", "fallido": "❌"}
ROL = {a: d["rol"] for a, d in AGENTES_EJECUTORES.items()}


@st.cache_resource(show_spinner="Cargando modelos, base de conocimiento y memoria…")
def cargar():
    return crear_agente()


def nueva_sesion():
    st.session_state.sesion = uuid.uuid4().hex[:8]
    st.session_state.mensajes = []


if "sesion" not in st.session_state:
    nueva_sesion()
agente = cargar()

# ------------------------------------------------------------------ barra lateral
with st.sidebar:
    st.header("👤 Estudiante")
    usuario = st.text_input("Alias", value="estudiante_demo",
                            help="Usa un alias: la memoria de largo plazo se asocia a él. No escribas tu nombre ni RUT.")
    st.caption(f"Sesión actual: `{st.session_state.sesion}`")
    if st.button("🆕 Nueva conversación", use_container_width=True,
                 help="Vacía la memoria de corto plazo. La de largo plazo (perfil y trámites) se mantiene."):
        nueva_sesion()
        st.rerun()

    st.header("📅 Condiciones")
    fecha = st.date_input("Fecha del calendario", value=rz.hoy(), format="DD-MM-YYYY",
                          help="Cámbiala para ver cómo el agente adapta el plan si un período está cerrado o próximo.")
    ver_traza = st.toggle("Mostrar razonamiento del agente", value=True)

    st.header("🧠 Memoria")
    perfil = agente.memoria.perfil(usuario)
    st.markdown("**Perfil (largo plazo)**  \n" + ("  \n".join(f"{k.capitalize()}: {v}" for k, v in perfil.items())
                                                  or "_sin datos_"))
    tramites = agente.memoria.tramites(usuario)
    st.markdown("**Trámites en curso (largo plazo)**  \n" + ("  \n".join(
        f"{NOMBRE_TRAMITE.get(t['tramite'], t['tramite'])}: *{etapa_legible(t['etapa'])}*" for t in tramites)
        or "_ninguno_"))
    tickets = agente.memoria.tickets(usuario)
    if tickets:
        st.markdown("**Tickets**  \n" + "  \n".join(f"{t['id']} ({t['estado']})" for t in tickets))
    n = len(agente.memoria.ventana(usuario, st.session_state.sesion))
    st.markdown(f"**Ventana de corto plazo:** {n} mensaje(s) · k = {agente.memoria.k} turnos")
    if st.button("🧹 Olvidar mis datos", use_container_width=True):
        r = agente.conversar("Borra mis datos", usuario, st.session_state.sesion, fecha)
        st.session_state.mensajes = [{"rol": "assistant", "texto": r.texto, "meta": asdict(r)}]
        st.rerun()

    st.divider()
    if hay_token():
        st.caption(f"🤖 LLM: {LLM_MODEL} (GitHub Models)" +
                   (f" · Manager: {LLM_MODEL_MANAGER}" if LLM_MODEL_MANAGER != LLM_MODEL else ""))
    else:
        st.caption("⚙️ Modo local sin token: planificación por reglas y respuestas extractivas.")


# ---------------------------------------------------------------------- mensajes
def mostrar_respuesta(meta: dict) -> None:
    replan = f" · 🔁 {meta['replanes']} replanificación(es)" if meta["replanes"] else ""
    st.caption(f"Estrategia **{meta['estrategia']}** · plan: {meta['metodo_plan'] or '—'} · "
               f"{len(meta['herramientas'])} herramienta(s){replan} · {meta['llamadas_llm']} llamada(s) al LLM · "
               f"{meta['latencia_ms'] / 1000:.1f} s" + (" · ➜ derivado a una persona" if meta["derivado"] else ""))
    if ver_traza and (meta["plan"] or meta["traza"]):
        with st.expander("🧭 Razonamiento del agente: plan, acciones y decisiones", expanded=False):
            if meta["objetivo"]:
                st.markdown(f"**Objetivo:** {meta['objetivo']}")
            if meta["plan"]:
                st.markdown("**Plan**")
                st.table([{"#": i + 1, "estado": ESTADO_PASO.get(p["estado"], p["estado"]) +
                           (" ➕" if p.get("agregado") else ""), "agente": ROL.get(p["agente"], p["agente"]),
                           "herramienta": p["herramienta"], "objetivo": p.get("motivo") or p["objetivo"]}
                          for i, p in enumerate(meta["plan"])])
            st.markdown("**Traza (pensamiento → acción → observación → decisión)**")
            st.markdown("\n".join(f"- {ICONOS.get(t['tipo'], '·')} {t['texto']}" for t in meta["traza"]))
    if meta["fuentes"]:
        with st.expander("📄 Fuentes"):
            st.markdown("\n".join(f"- {f}" for f in meta["fuentes"]))
    for archivo in meta["archivos"]:
        ruta = Path(archivo)
        if ruta.exists():
            st.download_button(f"⬇️ Descargar {ruta.name}", ruta.read_bytes(), file_name=ruta.name,
                               key=f"{archivo}-{uuid.uuid4().hex[:6]}")


st.title("🎓 Asistente Inteligente para Estudiantes Duoc UC")
st.caption("Proyecto académico ISY0101 · Agente con herramientas, memoria y planificación. Responde con documentos "
           "institucionales (simulados) y cita la fuente. No ingreses tu RUT ni datos personales.")

for m in st.session_state.mensajes:
    with st.chat_message(m["rol"]):
        st.markdown(m["texto"])
        if m.get("meta"):
            mostrar_respuesta(m["meta"])

if mensaje := st.chat_input("Escribe tu consulta… (ej.: Quiero empezar mi práctica, ¿cumplo los requisitos?)"):
    st.session_state.mensajes.append({"rol": "user", "texto": mensaje})
    with st.chat_message("user"):
        st.markdown(mensaje)
    with st.chat_message("assistant"):
        with st.spinner("El agente está planificando y usando sus herramientas…"):
            r = agente.conversar(mensaje, usuario, st.session_state.sesion, fecha)
        meta = asdict(r)
        st.markdown(r.texto)
        mostrar_respuesta(meta)
    st.session_state.mensajes.append({"rol": "assistant", "texto": r.texto, "meta": meta})
    st.rerun()
