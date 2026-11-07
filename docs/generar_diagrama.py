"""Genera docs/diagrama_arquitectura.png (python docs/generar_diagrama.py)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

W, H = 6.9, 4.5
fig, ax = plt.subplots(figsize=(W, H), dpi=300)
ax.set_xlim(0, 5); ax.set_ylim(0, 4); ax.axis("off")
FS = 5.6
C = {"dato": "#FFE9A8", "proc": "#DCE9F7", "ag": "#E4D7F5", "seg": "#F8D7D7",
     "llm": "#FFD8B5", "ok": "#C9E7D0", "hum": "#FFD0D0"}


def caja(c, r, txt, color, w=0.86, h=0.62):
    x, y = c + 0.5, 3.5 - r
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.015,rounding_size=0.06",
                                fc=color, ec="#444444", lw=0.6))
    ax.text(x, y, txt, ha="center", va="center", fontsize=FS, linespacing=1.15)
    return x, y, w, h


def flecha(a, b, lado_a, lado_b, estilo="-", color="#333333", txt=None, rad=0.0, off=(0, 0)):
    def punto(box, lado):
        x, y, w, h = box
        return {"r": (x + w / 2, y), "l": (x - w / 2, y), "t": (x, y + h / 2), "b": (x, y - h / 2)}[lado]
    pa, pb = punto(a, lado_a), punto(b, lado_b)
    ax.add_patch(FancyArrowPatch(pa, pb, arrowstyle="-|>", mutation_scale=6, lw=0.7, ls=estilo, color=color,
                                 connectionstyle=f"arc3,rad={rad}"))
    if txt:
        ax.text((pa[0] + pb[0]) / 2 + off[0], (pa[1] + pb[1]) / 2 + off[1], txt, fontsize=4.8, ha="center",
                color=color, style="italic")


# Fondos de zona
ax.add_patch(FancyBboxPatch((0.03, 2.72), 4.94, 1.22, boxstyle="round,pad=0.01,rounding_size=0.05",
                            fc="none", ec="#888888", lw=0.7, ls="--"))
ax.text(0.08, 3.88, "FASE OFFLINE · ingesta y actualización (src/ingest.py)", fontsize=5.6, weight="bold", va="top", color="#555555")
ax.add_patch(FancyBboxPatch((0.03, 0.02), 4.94, 2.62, boxstyle="round,pad=0.01,rounding_size=0.05",
                            fc="none", ec="#2F5D8A", lw=0.8))
ax.text(0.08, 2.58, "FASE ONLINE · consulta del estudiante", fontsize=5.6, weight="bold", va="top", color="#2F5D8A")

# Fase offline (fila 0 -> y=3.3)
def caja_y(c, y, txt, color, w=0.86, h=0.56, shape=None):
    x = c + 0.5
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.015,rounding_size=0.06",
                                fc=color, ec="#444444", lw=0.6))
    ax.text(x, y, txt, ha="center", va="center", fontsize=FS, linespacing=1.15)
    return x, y, w, h

d1 = caja_y(0, 3.28, "Docs internos (5)\n+ externos (2)\nmanifest.json", C["dato"])
d2 = caja_y(1, 3.28, "Chunking\nMarkdown + Recursive\n800 / overlap 120", C["proc"])
d3 = caja_y(2, 3.28, "Embeddings locales\nMiniLM multilingüe\n(normalizados)", C["proc"])
d4 = caja_y(3, 3.28, "Metadatos\nárea · origen\nversión · sección", C["proc"])
d5 = caja_y(4, 3.28, "ChromaDB\nsimilitud coseno\nre-indexación por hash", C["ok"])
for a, b in [(d1, d2), (d2, d3), (d3, d4), (d4, d5)]:
    flecha(a, b, "r", "l")

# Fase online
Y1, Y2, Y3 = 2.12, 1.30, 0.50
u = caja_y(0, Y1, "Estudiante\nStreamlit / CLI", "#FFFFFF")
g = caja_y(1, Y1, "1 Guardrails\nenmascara RUT\nanti-injection", C["seg"])
co = caja_y(2, Y1, "2 Agente\nCoordinador\nárea + carrera", C["ag"])
ag = caja_y(3, Y1, "3 Agente especialista\nAcadémico · Admin.\nPráctica/Tit. · TI", C["ag"])
rt = caja_y(4, Y1, "4 Retriever\nfiltro por área\n4 int. + 2 ext.\numbral relevancia", C["proc"], h=0.66)
llm = caja_y(4, Y2, "5 LLM GPT-4o-mini\ntemp. 0 · solo\ncontexto [F1..Fn]", C["llm"])
ver = caja_y(3, Y2, "6 Verificación\n¿SIN_INFORMACION?\ncitas → fuentes", C["seg"])
out = caja_y(2, Y2, "Respuesta con\nfuentes citadas\n[1] Doc – Sección", C["ok"])
der = caja_y(1, Y3, "Agente de\nDerivación", C["ag"])
hum = caja_y(0, Y3, "Atención humana\nCoordinación · Punto\nEstud. · Mesa TI", C["hum"])
log = caja_y(3, Y3, "Registro de uso\n(sin datos\npersonales)", "#F2F2F2")

for a, b in [(u, g), (g, co), (co, ag), (ag, rt)]:
    flecha(a, b, "r", "l")
flecha(rt, llm, "b", "t"); flecha(llm, ver, "l", "r"); flecha(ver, out, "l", "r")
flecha(d5, rt, "b", "t", txt="top-k", off=(0.14, 0))
flecha(ver, der, "b", "r", estilo="--", color="#B03030", txt="sin evidencia", rad=0.0, off=(0.1, 0.1))
flecha(g, der, "b", "t", estilo="--", color="#B03030", txt="sensible /\nexcepcional", off=(0.28, 0.1))
flecha(der, hum, "l", "r", estilo="--", color="#B03030")
flecha(ver, log, "b", "t", estilo=":", color="#777777")

fig.savefig("docs/diagrama_arquitectura.png", bbox_inches="tight", pad_inches=0.03)
print("ok")
