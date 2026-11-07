"""Genera los diagramas de la EP2 en docs/ (python docs/generar_diagramas_ep2.py)."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

DOCS = Path(__file__).resolve().parent
C = {"dato": "#FFE9A8", "proc": "#DCE9F7", "ag": "#E4D7F5", "seg": "#F8D7D7", "llm": "#FFD8B5", "ok": "#C9E7D0",
     "mem": "#D5EFEF", "gris": "#F2F2F2", "blanco": "#FFFFFF"}
ROJO, AZUL, GRIS = "#B03030", "#2F5D8A", "#555555"


class Lienzo:
    def __init__(self, ancho, alto, xmax, ymax, fs=5.6):
        self.fig, self.ax = plt.subplots(figsize=(ancho, alto), dpi=300)
        self.ax.set_xlim(0, xmax)
        self.ax.set_ylim(0, ymax)
        self.ax.axis("off")
        self.fs = fs

    def caja(self, x, y, txt, color, w=1.8, h=0.8, titulo=True, lw=0.6, fs=None):
        self.ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, lw=lw, fc=color, ec="#444444",
                                         boxstyle="round,pad=0.02,rounding_size=0.08"))
        lineas = txt.split("\n")
        if titulo and len(lineas) > 1:
            self.ax.text(x, y + h / 2 - 0.1, lineas[0], ha="center", va="top", fontsize=fs or self.fs, weight="bold")
            self.ax.text(x, y - 0.06, "\n".join(lineas[1:]), ha="center", va="center", fontsize=(fs or self.fs) - 0.6,
                         linespacing=1.2)
        else:
            self.ax.text(x, y, txt, ha="center", va="center", fontsize=fs or self.fs, weight="bold" if titulo else None)
        return (x, y, w, h)

    def zona(self, x0, y0, x1, y1, titulo, color=GRIS, ls="--"):
        self.ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0.01,rounding_size=0.08",
                                         fc="none", ec=color, lw=0.8, ls=ls))
        self.ax.text(x0 + 0.08, y1 - 0.08, titulo, fontsize=self.fs, weight="bold", va="top", color=color)

    @staticmethod
    def _punto(caja, lado, desp=0.0):
        x, y, w, h = caja
        return {"r": (x + w / 2, y + desp), "l": (x - w / 2, y + desp), "t": (x + desp, y + h / 2),
                "b": (x + desp, y - h / 2)}[lado]

    def flecha(self, a, b, la, lb, txt=None, color="#333333", ls="-", rad=0.0, off=(0, 0), da=0.0, db=0.0, doble=False):
        pa, pb = self._punto(a, la, da), self._punto(b, lb, db)
        self.ax.add_patch(FancyArrowPatch(pa, pb, arrowstyle="<|-|>" if doble else "-|>", mutation_scale=7, lw=0.8,
                                          ls=ls, color=color, connectionstyle=f"arc3,rad={rad}"))
        if txt:
            self.ax.text((pa[0] + pb[0]) / 2 + off[0], (pa[1] + pb[1]) / 2 + off[1], txt, fontsize=self.fs - 0.8,
                         ha="center", va="center", color=color, style="italic",
                         bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9))

    def guardar(self, nombre):
        self.fig.savefig(DOCS / nombre, bbox_inches="tight", pad_inches=0.04)
        plt.close(self.fig)
        print("ok", nombre)


def orquestacion():
    L = Lienzo(7.6, 5.6, 10, 7.4)
    e = L.caja(0.85, 6.75, "Estudiante\nStreamlit · CLI", C["blanco"], w=1.4, h=0.75)
    g = L.caja(2.78, 6.75, "Guardrails (EP1)\nenmascara RUT y correo · bloquea\ninyección y temas delicados", C["seg"],
               w=2.2, h=0.75)
    r = L.caja(5.05, 6.75, "Recordar (memoria)\nventana k turnos · plan pausado\nperfil · trámites · episodios", C["mem"],
               w=2.1, h=0.75)
    m = L.caja(7.85, 6.75, "Agente Manager\nelige la estrategia y valida\nlos resultados (sin herramientas)", C["ag"],
               w=2.3, h=0.75, lw=1.0)
    for a, b in ((e, g), (g, r), (r, m)):
        L.flecha(a, b, "r", "l")

    L.zona(0.1, 4.45, 9.9, 5.95, "", AZUL, ls="-")
    L.ax.text(0.18, 4.52, "Estrategia que decide el Manager según la solicitud", fontsize=L.fs, weight="bold",
              color=AZUL, va="bottom")
    d = L.caja(1.35, 5.2, "Directa\npolítica determinista\ncaso excepcional · borrar datos", C["seg"], w=2.3, h=0.75)
    re_ = L.caja(4.75, 5.2, "Reactiva · ReAct\nAgentExecutor + function calling\nThought → Action → Observation (máx. 4)",
                 C["llm"], w=3.0, h=0.75)
    p = L.caja(8.25, 5.2, "Planificada · Plan-and-Execute\nplan completo antes de actuar\nLLM (function calling) o reglas",
               C["llm"], w=2.95, h=0.75)
    L.flecha(m, d, "b", "t", txt="acción crítica", off=(0.2, 0.12), da=-0.95)
    L.flecha(m, re_, "b", "t", txt="consulta puntual", off=(0.25, 0.1), da=-0.45)
    L.flecha(m, p, "b", "t", txt="trámite de varios pasos", off=(0.05, 0.05), da=0.35)

    v = L.caja(8.25, 3.75, "Validación del Manager\ncontinuar · reintentar · pedir dato\n"
               "replanificar (omitir · agregar · modificar)", C["seg"], w=2.95, h=0.8)
    L.flecha(p, v, "b", "t", doble=True, txt="cada paso", off=(0.42, 0))
    L.flecha(re_, v, "r", "l", da=-0.2, db=0.15, color=AZUL, txt="respuesta", off=(0.0, 0.12), rad=0.15)

    L.zona(0.1, 1.85, 7.05, 3.35, "", GRIS)
    L.ax.text(0.18, 3.3, "Agentes ejecutores (cada uno con sus herramientas)", fontsize=L.fs, weight="bold",
              color=GRIS, va="top")
    w = L.caja(1.25, 2.45, "Agente de Escritura\nredactar_solicitud\nregistrar_derivacion\nguardar_tramite · olvido",
               C["proc"], w=2.0, h=1.0)
    c = L.caja(3.55, 2.45, "Agente de Consulta\nbuscar_normativa\nconsultar_calendario\nconsultar_mis_tramites",
               C["proc"], w=2.0, h=1.0)
    z = L.caja(5.85, 2.45, "Agente de Razonamiento\nverificar_requisitos_practica\ncalcular_asistencia\n"
               "calcular_nota_necesaria", C["proc"], w=2.2, h=1.0)
    L.flecha(d, w, "b", "t", ls="--", color=ROJO)
    L.flecha(re_, c, "b", "t", da=-0.6, color=AZUL)
    L.flecha(re_, z, "b", "t", da=0.6, color=AZUL, txt="solo lectura", off=(0.5, 0.0))
    L.flecha(v, z, "l", "r", txt="delega el paso", off=(0.05, 0.12))

    mem = L.caja(1.25, 0.7, "Memoria y salidas\nSQLite (corto y largo plazo)\nChroma episódica · borradores",
                 C["mem"], w=2.2, h=0.85)
    rag = L.caja(3.55, 0.7, "RAG multiagente (EP1)\nCoordinador + 4 especialistas\nChromaDB · citas por código",
                 C["ok"], w=2.2, h=0.85)
    dat = L.caja(5.85, 0.7, "Reglas y calendario\nreglas_academicas.json\ncalendario (simulado)", C["dato"], w=2.0, h=0.85)
    L.flecha(w, mem, "b", "t")
    L.flecha(c, rag, "b", "t")
    L.flecha(z, dat, "b", "t")
    L.flecha(c, mem, "b", "t", da=-0.6, db=0.6, ls=":", color=GRIS)

    s = L.caja(8.55, 2.45, "Síntesis\nrespuesta con las salidas\nfuentes numeradas por código", C["ok"], w=2.4, h=0.85)
    mz = L.caja(8.55, 1.15, "Memorizar\nventana · estado de sesión\ntrámite · episodio · traza", C["mem"], w=2.4, h=0.8)
    L.flecha(v, s, "b", "t", txt="finalizar", off=(0.32, 0), da=0.3)
    L.flecha(s, mz, "b", "t")
    L.ax.text(8.55, 0.42, "→ Respuesta + plan + traza en la interfaz", ha="center", fontsize=L.fs - 0.4, color=AZUL,
              weight="bold")
    L.guardar("diagrama_orquestacion_ep2.png")


def memoria():
    L = Lienzo(7.4, 3.9, 10, 5.3)
    L.zona(0.1, 0.65, 4.6, 5.2, "Corto plazo · por sesión (usuario::sesión)", AZUL, ls="-")
    L.zona(5.4, 0.65, 9.9, 5.2, "Largo plazo · por estudiante (entre sesiones)", "#2E7D5B", ls="-")
    v = L.caja(2.35, 4.25, "ConversationBufferWindowMemory\nk turnos (VENTANA_MEMORIA)\nes lo que se inyecta en el prompt",
               C["mem"], w=3.9, h=0.85)
    h = L.caja(2.35, 2.85, "HistorialSQLite (BaseChatMessageHistory)\nHumanMessage / AIMessage completos\n"
               "persisten aunque se reinicie la app", C["mem"], w=3.9, h=0.85)
    e = L.caja(2.35, 1.45, "Estado de la sesión\ntema activo (preguntas de seguimiento)\nplan pausado + dato que falta",
               C["mem"], w=3.9, h=0.85)
    L.flecha(v, h, "b", "t", txt="chat_memory", off=(0.55, 0))
    p = L.caja(7.65, 4.25, "Perfil declarado (SQLite)\ncarrera · sede · jornada\ncondición cambiante si la carrera cambia",
               C["ok"], w=3.9, h=0.85)
    t = L.caja(7.65, 2.85, "Trámites y tickets (SQLite)\netapa + próximo paso de cada trámite\n"
               "códigos de derivación", C["ok"], w=3.9, h=0.85)
    ep = L.caja(7.65, 1.45, "Memoria episódica (Chroma propia)\nresumen anonimizado de cada consulta\n"
                "recuperación por similitud y por estudiante", C["ok"], w=3.9, h=0.85)
    L.ax.text(5.0, 0.3, "Privacidad (Ley 19.628 / 21.719): solo texto enmascarado · cifras anonimizadas en largo plazo · "
              "alias en vez de identidad · «Borra mis datos» elimina todo", ha="center", fontsize=L.fs - 0.3,
              color=ROJO, style="italic")
    L.ax.annotate("", xy=(5.38, 3.55), xytext=(4.62, 3.55), arrowprops=dict(arrowstyle="<|-|>", lw=0.8, color=GRIS))
    L.ax.text(5.0, 3.72, "agente", ha="center", fontsize=L.fs - 0.6, color=GRIS, style="italic")
    L.guardar("diagrama_memoria_ep2.png")


def decisiones():
    L = Lienzo(7.4, 3.2, 10, 5.1, fs=5.4)
    L.ax.set_ylim(0.6, 5.1)
    pl = L.caja(0.95, 3.9, "Plan\npasos con agente,\nherramienta y objetivo", C["llm"], w=1.6, h=0.8)
    ej = L.caja(2.85, 3.9, "Ejecutor\ncompleta argumentos\ncon la memoria", C["proc"], w=1.7, h=0.8)
    ob = L.caja(4.75, 3.9, "Observación\nresultado de la\nherramienta", C["gris"], w=1.6, h=0.8)
    ma = L.caja(7.2, 3.9, "Manager evalúa el resultado\nmáx. 8 herramientas\ny 3 replanificaciones", C["ag"], w=2.6,
                h=0.8, lw=1.0)
    for a, b in ((pl, ej), (ej, ob), (ob, ma)):
        L.flecha(a, b, "r", "l")
    filas = [
        ("Falla técnica", "reintenta 1 vez; si persiste,\ncancela y deriva con ticket", C["seg"]),
        ("Falta un dato", "pausa el plan, pregunta y lo\nreanuda en el turno siguiente", C["mem"]),
        ("Sin evidencia", "no redacta nada sin fuente;\nagrega registrar_derivacion", C["seg"]),
        ("No cumple", "omite calendario y solicitud;\netapa «cumplir requisitos»", C["dato"]),
        ("Período no abierto", "omite la solicitud;\netapa «esperar apertura»", C["dato"]),
        ("Riesgo de reprobar", "agrega el paso: qué pasa\nsi repruebo (reglamento)", C["dato"]),
    ]
    xs = [0.85 + i * 1.66 for i in range(6)]
    for x, (cond, accion, color) in zip(xs, filas):
        b = L.caja(x, 1.75, f"{cond}\n{accion}", color, w=1.58, h=1.0, fs=5.2)
        L.flecha(ma, b, "b", "t", da=(x - 7.2) * 0.12, color=GRIS, rad=0.0)
    L.ax.text(5.0, 0.85, "Sin condición especial: continúa con el siguiente paso pendiente · al terminar: síntesis "
              "con fuentes y memoria", ha="center", fontsize=L.fs - 0.2, color=AZUL, style="italic")
    L.flecha(ma, ej, "t", "t", rad=0.25, txt="siguiente paso / reintento", off=(0, 0.3), color=AZUL)
    L.guardar("diagrama_decisiones_ep2.png")


if __name__ == "__main__":
    orquestacion()
    memoria()
    decisiones()
