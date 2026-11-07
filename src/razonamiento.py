"""Razonamiento determinista que usan las herramientas del agente.

El LLM decide CUÁNDO calcular y con qué datos; la aritmética y la comparación con las reglas las
hace este código, porque un porcentaje mal calculado puede llevar a una mala decisión del
estudiante. Las reglas vienen de datos/reglas_academicas.json y del calendario simulado."""
import json
import math
from datetime import date
from functools import lru_cache

from .config import CALENDARIO_PATH, FECHA_SIMULADA, REGLAS_PATH


@lru_cache(maxsize=1)
def reglas() -> dict:
    return json.loads(REGLAS_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def calendario() -> dict:
    return json.loads(CALENDARIO_PATH.read_text(encoding="utf-8"))


def hoy() -> date:
    """Fecha del sistema, o FECHA_SIMULADA para demos reproducibles."""
    return date.fromisoformat(FECHA_SIMULADA) if FECHA_SIMULADA else date.today()


def _pct(x: float) -> str:
    """72 -> '72', 66.666 -> '66,7' (porcentajes)."""
    return f"{round(x, 1):g}".replace(".", ",")


def _nota(x: float, decimales: int = 1) -> str:
    """4 -> '4,0' (notas en escala chilena)."""
    return f"{x:.{decimales}f}".replace(".", ",")


# ------------------------------------------------------------------ práctica
def evaluar_requisitos_practica(carrera: str, avance_malla: float) -> dict:
    tabla = reglas()["practica"]
    regla = tabla["carreras"].get(carrera)
    if regla is None:
        return {"sin_regla": True, "carrera": carrera,
                "mensaje": f"No tengo registrada la regla de práctica para {carrera}."}
    if not regla["gestion_individual"]:
        return {"cumple": None, "gestion_individual": False, "carrera": carrera, "fuente": tabla["fuente"],
                "mensaje": f"En {carrera} la práctica se realiza en campos clínicos que asigna la carrera; "
                           "no se inscribe de forma individual."}
    minimo = regla["avance_minimo"]
    cumple = avance_malla >= minimo
    extra = f" ({regla['condicion_extra']})" if regla.get("condicion_extra") else ""
    if cumple:
        mensaje = (f"✅ Cumples el avance de malla: llevas {_pct(avance_malla)} % y {carrera} exige "
                   f"{minimo} %{extra}. La práctica dura {regla['horas']} horas.")
    else:
        mensaje = (f"❌ Todavía no cumples el avance de malla: llevas {_pct(avance_malla)} % y {carrera} exige "
                   f"{minimo} %{extra}; te faltan {_pct(minimo - avance_malla)} puntos porcentuales.")
    return {"cumple": cumple, "gestion_individual": True, "carrera": carrera, "avance_minimo": minimo,
            "horas": regla["horas"], "mensaje": mensaje, "fuente": tabla["fuente"]}


# ----------------------------------------------------------------- asistencia
def calcular_asistencia(clases_totales: int, inasistencias: int, tipo: str = "teorica") -> dict:
    r = reglas()["asistencia"]
    minimo = r["minimo_practica"] if tipo == "practica" else r["minimo_teorica"]
    asistencia = 100 * (clases_totales - inasistencias) / clases_totales
    max_faltas = math.floor(clases_totales * (100 - minimo) / 100)
    restantes = max_faltas - inasistencias
    cumple = asistencia >= minimo
    tipo_txt = "talleres y asignaturas prácticas" if tipo == "practica" else "asignaturas teóricas"
    if cumple:
        mensaje = (f"Tu asistencia es {_pct(asistencia)} %: cumples el mínimo de {minimo} % que se exige en "
                   f"{tipo_txt}. Puedes faltar como máximo a {restantes} clase(s) más.")
    else:
        mensaje = (f"⚠️ Tu asistencia es {_pct(asistencia)} %: está bajo el mínimo de {minimo} % que se exige en "
                   f"{tipo_txt}. Con {inasistencias} inasistencias superas el máximo permitido ({max_faltas}).")
    return {"asistencia": round(asistencia, 1), "minimo": minimo, "cumple": cumple,
            "faltas_restantes": max(restantes, 0), "mensaje": mensaje, "fuente": r["fuente"]}


# ---------------------------------------------------------------------- notas
def calcular_nota_necesaria(notas: list) -> dict:
    r = reglas()["aprobacion"]
    minima, maxima = r["nota_minima"], r["nota_maxima"]
    peso = sum(n["ponderacion"] for n in notas)
    if peso > 100:
        return {"error": "las ponderaciones suman más de 100 %"}
    acumulado = sum(n["nota"] * n["ponderacion"] / 100 for n in notas)
    restante = 100 - peso
    if restante <= 0:
        aprobado = round(acumulado, 1) >= minima
        mensaje = (f"Tu nota final es {_nota(acumulado)}: "
                   + ("apruebas." if aprobado else f"no alcanza el {_nota(minima)} para aprobar."))
        return {"nota_final": round(acumulado, 1), "alcanzable": aprobado, "mensaje": mensaje, "fuente": r["fuente"]}
    necesaria = max((minima - acumulado) / (restante / 100), 1.0)
    alcanzable = necesaria <= maxima
    if alcanzable:
        mensaje = (f"Llevas {_nota(acumulado, 2)} puntos acumulados con el {_pct(peso)} % evaluado. "
                   f"Para aprobar con {_nota(minima)} necesitas un promedio de {_nota(necesaria)} en el "
                   f"{_pct(restante)} % restante.")
    else:
        mensaje = (f"⚠️ Con el {_pct(peso)} % evaluado necesitarías un {_nota(necesaria)} en el "
                   f"{_pct(restante)} % restante, sobre la nota máxima ({_nota(maxima)}): ya no es posible aprobar "
                   "con las evaluaciones que quedan.")
    return {"acumulado": round(acumulado, 2), "porcentaje_restante": restante, "nota_necesaria": round(necesaria, 1),
            "alcanzable": alcanzable, "mensaje": mensaje, "fuente": r["fuente"]}


# ------------------------------------------------------------------ calendario
def estado_periodo(evento: str, fecha: date) -> dict:
    cal = calendario()
    ev = cal["eventos"][evento]
    inicio, fin = date.fromisoformat(ev["inicio"]), date.fromisoformat(ev["fin"])
    if fecha < inicio:
        estado, detalle = "proximo", f"abre en {(inicio - fecha).days} día(s)"
    elif fecha > fin:
        estado, detalle = "cerrado", "ya cerró este semestre"
    else:
        estado, detalle = "abierto", f"quedan {(fin - fecha).days} día(s) para el cierre"
    icono, texto = {"abierto": ("🟢", "abierta"), "proximo": ("🟡", "aún no abre"), "cerrado": ("🔴", "cerrada")}[estado]
    mensaje = (f"{icono} {ev['nombre']}: **{texto}** ({detalle}). Período: {inicio:%d-%m-%Y} al {fin:%d-%m-%Y}, "
               f"en {ev['donde']}. Fecha considerada: {fecha:%d-%m-%Y}.")
    return {"evento": evento, "estado": estado, "inicio": ev["inicio"], "fin": ev["fin"], "mensaje": mensaje,
            "fuente": cal["fuente"]}
