"""Boceto (wireframe) de la interfaz: python docs/generar_boceto.py"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=200)
ax.set_xlim(0, 16); ax.set_ylim(0, 10.5); ax.axis("off")
def box(x, y, w, h, fc="white", ec="#444", lw=0.8, r=0.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw))
box(0.1, 0.1, 15.8, 10.3, "#FAFAFA")
ax.text(0.5, 9.8, "Asistente Inteligente para Estudiantes Duoc UC", fontsize=8, weight="bold", va="center")
box(0.3, 0.4, 4.2, 8.6, "#EEF3F9")
ax.text(0.6, 8.6, "Tu contexto (opcional)", fontsize=6.5, weight="bold")
box(0.6, 7.4, 3.6, 0.8, "white"); ax.text(0.8, 7.8, "Carrera: Ing. Informática ▾", fontsize=6, va="center")
ax.text(0.6, 6.6, "Los procedimientos cambian\nsegún carrera o sede.", fontsize=5.4, va="top", color="#555")
box(0.6, 0.8, 3.6, 0.8, "#E8E8E8"); ax.text(2.4, 1.2, "Nueva conversación", fontsize=6, ha="center", va="center")
box(4.8, 6.6, 6.6, 1.3, "#DCE9F7"); ax.text(5.0, 7.25, "¿Qué necesito para comenzar mi\npráctica profesional?", fontsize=6.2, va="center")
box(4.8, 2.6, 10.8, 3.7, "white")
ax.text(5.0, 6.0, "Para iniciar tu práctica en Ingeniería en Informática necesitas: ser alumno regular,", fontsize=5.4, va="top")
ax.text(5.0, 5.55, "haber aprobado el 80 % de la malla [1], contar con empresa y seguro vigente [2].", fontsize=5.4, va="top")
ax.text(5.0, 4.85, "Área: Práctica y titulación · confianza del enrutador: 95 %", fontsize=5, color="#666", va="top")
box(5.0, 2.8, 3.4, 0.9, "#F3F3F3"); ax.text(5.2, 3.25, "Fuentes  ▾", fontsize=5.8, va="center")
box(4.8, 0.6, 10.8, 1.2, "white"); ax.text(5.0, 1.2, "Escribe tu consulta…", fontsize=6, color="#888", va="center")
ax.text(15.3, 1.2, ">", fontsize=9, ha="right", va="center")
ax.text(0.5, 0.0, "Boceto v1 – interfaz de chat (Streamlit)", fontsize=5, color="#777")
fig.savefig("docs/boceto_interfaz.png", bbox_inches="tight", pad_inches=0.05)
