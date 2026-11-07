"""Planificación y toma de decisiones del Agente Manager (EP2, IE5), según la clase 2.3.1.

1. elegir_estrategia(): el Manager decide CÓMO resolver la solicitud.
   - reactiva   (ReAct): consultas puntuales; el agente decide la acción paso a paso.
   - planificada (Plan-and-Execute): trámites de varios pasos; se arma el plan completo ANTES de actuar.
   - directa: acciones críticas (casos excepcionales, borrar datos), siempre por reglas.
2. planificar(): descompone el objetivo en pasos (agente ejecutor + herramienta + argumentos).
   Con LLM, el plan se pide por function calling (salida estructurada Pydantic); sin LLM, o si el
   plan del LLM no es válido, se usa el planificador por reglas.
3. evaluar_paso(): después de cada paso el Manager valida el resultado (orquestación jerárquica) y
   decide continuar, reintentar, pausar para pedir un dato o REPLANIFICAR (omitir, agregar o
   modificar pasos) cuando cambian las condiciones. Es determinista para que sea explicable y probable.
Límites de costo (clase 2.3.1): MAX_ITERACIONES herramientas y MAX_REPLANES replanificaciones por turno.
"""
import copy
import re
from typing import Callable, Optional

from pydantic import BaseModel, Field

from . import guardrails, router
from .config import MAX_ITERACIONES, MAX_REPLANES
from .extraccion import extraer_asistencia, extraer_notas
from .guardrails import normalizar
from .herramientas import AGENTE_DE, ETAPAS, NO_PLANIFICABLES

MAX_PASOS_PLAN = 6
TRAMITES = ("practica", "titulacion", "suspension", "retiro", "justificacion")


def paso(herramienta: str, objetivo: str, **args) -> dict:
    return {"agente": AGENTE_DE.get(herramienta, "?"), "herramienta": herramienta, "args": args,
            "objetivo": objetivo, "estado": "pendiente"}


# ================================================================= intención
def _hay(n: str, *claves) -> bool:
    return any(c in n for c in claves)


_PIDE_DOCUMENTO = re.compile(r"\b(redacta\w*|prepara\w*|borrador|hazme|escribe\w*|formulario|genera(r|me|la)?|"
                             r"llenar la solicitud|ayudame con la solicitud)\b")
_ACCION = ("quiero empezar", "quiero comenzar", "quiero iniciar", "quiero inscribir", "quiero hacer",
           "quiero pedir", "quiero solicitar", "quiero suspender", "quiero retirar", "quiero justificar",
           "empezar mi", "comenzar mi", "iniciar mi", "inscribir mi", "postular", "ayudame", "cumplo",
           "puedo empezar", "puedo comenzar", "puedo iniciar", "puedo inscribir", "necesito suspender",
           "necesito retirar", "necesito justificar", "como pido", "como solicito")


def pide_documento(consulta: str) -> bool:
    return bool(_PIDE_DOCUMENTO.search(normalizar(consulta)))


def identificar_evento(consulta: str) -> Optional[str]:
    n = normalizar(consulta)
    for clave, evento in (("practica", "inscripcion_practica"), ("titul", "inscripcion_titulacion"),
                          ("retir", "retiro_asignaturas"), ("suspen", "suspension_estudios"),
                          ("examen", "examenes_finales")):
        if clave in n:
            return evento
    return None


def detectar_intencion(consulta: str) -> str:
    n = normalizar(consulta)
    if _hay(n, "olvida mis datos", "borra mis datos", "elimina mis datos", "borrar mis datos", "olvidame"):
        return "olvidar"
    if _hay(n, "en que quede", "en que voy", "mis tramites", "mi tramite", "mis tickets", "mi ticket",
            "que me falta", "como va mi", "estado de mi", "donde quede"):
        return "seguimiento"
    if guardrails.es_caso_excepcional(consulta):
        return "excepcional"
    accion = _hay(n, *_ACCION) or pide_documento(consulta)
    if "practica" in n and accion:
        return "practica"
    if _hay(n, "titulacion", "titularme", "titulo") and accion:
        return "titulacion"
    if "suspen" in n and accion:
        return "suspension"
    if "retir" in n and accion:
        return "retiro"
    if "justific" in n and accion:
        return "justificacion"
    if extraer_asistencia(consulta):
        return "asistencia"
    if extraer_notas(consulta):
        return "nota"
    if identificar_evento(consulta) and _hay(n, "cuando", "fecha", "plazo", "periodo", "abiert", "cierra", "hasta"):
        return "calendario"
    return "consulta"


def elegir_estrategia(intencion: str) -> tuple:
    """(estrategia, motivo) según la complejidad de la solicitud."""
    if intencion in ("olvidar", "excepcional"):
        return "directa", "acción crítica: la resuelve la política del Manager, sin delegar en el LLM"
    if intencion in TRAMITES or intencion == "seguimiento":
        return "planificada", ("trámite de varios pasos: conviene ver el plan completo antes de actuar "
                               "(Plan-and-Execute)")
    return "reactiva", "consulta puntual: basta decidir la acción paso a paso (ReAct)"


# =================================================================== reglas
_OBJETIVOS = {
    "practica": "Iniciar la práctica profesional", "titulacion": "Iniciar el proceso de titulación",
    "suspension": "Gestionar la suspensión de estudios", "retiro": "Gestionar el retiro de una asignatura",
    "justificacion": "Justificar una inasistencia", "seguimiento": "Retomar los trámites en curso",
    "olvidar": "Borrar los datos del estudiante", "excepcional": "Derivar un caso excepcional a una persona",
    "asistencia": "Calcular la situación de asistencia", "nota": "Calcular la nota necesaria para aprobar",
    "calendario": "Informar un período del calendario", "consulta": "Responder una consulta con documentos",
}


def planificar_por_reglas(consulta: str, intencion: str, datos: Optional[dict] = None) -> list:
    """Plan determinista para cada intención (respaldo sin LLM y política de las acciones críticas)."""
    datos = datos or {}
    doc = pide_documento(consulta)
    etapa = "entregar_solicitud" if doc else "reunir_documentos"
    if intencion == "olvidar":
        return [paso("olvidar_mis_datos", "ejercer el derecho de supresión")]
    if intencion == "seguimiento":
        return [paso("consultar_mis_tramites", "leer los trámites y tickets guardados")]
    if intencion == "excepcional":
        area, _ = router.clasificar_por_palabras(consulta)
        return [paso("registrar_derivacion", "dejar el caso en manos de una persona",
                     area=area if area != "otro" else "academico", resumen=consulta)]
    if intencion == "practica":
        pasos = [paso("verificar_requisitos_practica", "comprobar el avance de malla mínimo de la carrera",
                      avance_malla=datos.get("avance_malla")),
                 paso("buscar_normativa", "obtener documentos y pasos con su fuente",
                      pregunta="¿Qué documentos y pasos necesito para inscribir la práctica profesional?",
                      area="practica_titulacion"),
                 paso("consultar_calendario", "verificar que la inscripción esté abierta", evento="inscripcion_practica")]
        if doc:
            pasos.append(paso("redactar_solicitud", "preparar el borrador de inscripción", tipo="inscripcion_practica"))
        return pasos + [paso("guardar_tramite", "recordar la etapa para otra sesión", tramite="practica", etapa=etapa)]
    if intencion == "titulacion":
        pasos = [paso("buscar_normativa", "obtener requisitos y documentos de titulación",
                      pregunta="¿Qué requisitos y documentos necesito para iniciar el proceso de titulación?",
                      area="practica_titulacion"),
                 paso("consultar_calendario", "verificar que la inscripción esté abierta",
                      evento="inscripcion_titulacion")]
        if doc:
            pasos.append(paso("redactar_solicitud", "preparar el borrador de inscripción", tipo="inscripcion_titulacion"))
        return pasos + [paso("guardar_tramite", "recordar la etapa para otra sesión", tramite="titulacion", etapa=etapa)]
    if intencion in ("suspension", "retiro"):
        evento, tipo = {"suspension": ("suspension_estudios", "suspension_estudios"),
                        "retiro": ("retiro_asignaturas", "retiro_asignaturas")}[intencion]
        pasos = [paso("buscar_normativa", "obtener el procedimiento con su fuente", pregunta=consulta,
                      area="administrativo"),
                 paso("consultar_calendario", "verificar que el período esté abierto", evento=evento)]
        if doc:
            pasos.append(paso("redactar_solicitud", "preparar el borrador de solicitud", tipo=tipo))
        return pasos + [paso("guardar_tramite", "recordar la etapa para otra sesión", tramite=intencion, etapa=etapa)]
    if intencion == "justificacion":
        pasos = [paso("buscar_normativa", "obtener el procedimiento de justificación",
                      pregunta="¿Cómo justifico una inasistencia a una evaluación?", area="academico")]
        if doc:
            pasos += [paso("redactar_solicitud", "preparar la justificación", tipo="justificacion_inasistencia"),
                      paso("guardar_tramite", "recordar la etapa para otra sesión", tramite="justificacion",
                           etapa="entregar_solicitud")]
        return pasos
    if intencion == "asistencia":
        return [paso("calcular_asistencia", "calcular el % de asistencia y las faltas restantes",
                     **extraer_asistencia(consulta)),
                paso("buscar_normativa", "citar la regla de asistencia mínima",
                     pregunta="¿Cuál es la asistencia mínima para aprobar una asignatura?", area="academico")]
    if intencion == "nota":
        return [paso("calcular_nota_necesaria", "calcular la nota mínima en lo que resta",
                     notas=extraer_notas(consulta)),
                paso("buscar_normativa", "citar la nota de aprobación",
                     pregunta="¿Con qué nota se aprueba una asignatura?", area="academico")]
    if intencion == "calendario":
        return [paso("consultar_calendario", "consultar el período en el calendario",
                     evento=identificar_evento(consulta))]
    return [paso("buscar_normativa", "responder con documentos citados", pregunta=consulta)]


# ====================================================================== LLM
class PasoLLM(BaseModel):
    herramienta: str = Field(description="Nombre exacto de una herramienta disponible")
    objetivo: str = Field(description="Para qué sirve este paso, en máximo 12 palabras")
    argumentos: dict = Field(default_factory=dict, description="Argumentos de la herramienta")


class PlanLLM(BaseModel):
    """Plan de acción del Agente Manager."""
    objetivo: str = Field(description="Objetivo del estudiante en una frase")
    pasos: list[PasoLLM] = Field(description=f"Pasos en orden, máximo {MAX_PASOS_PLAN}")


def crear_planificador_llm(chat_llm, herramientas: dict) -> Callable:
    """Planificador con function calling: el LLM devuelve un PlanLLM validado por Pydantic."""
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    from .prompts import PLANIFICADOR_SYSTEM, PLANIFICADOR_USER
    catalogo = "\n".join(f"- {h.name}({', '.join(h.args_schema.model_fields)}): {h.description}"
                         for nombre, h in herramientas.items() if nombre not in NO_PLANIFICABLES)
    prompt = ChatPromptTemplate.from_messages([
        ("system", PLANIFICADOR_SYSTEM), MessagesPlaceholder("chat_history"), ("human", PLANIFICADOR_USER)])
    cadena = prompt | chat_llm.with_structured_output(PlanLLM, method="function_calling")

    def planificar_llm(consulta: str, contexto: dict) -> Optional[PlanLLM]:
        return cadena.invoke({"catalogo": catalogo, "chat_history": contexto.get("ventana", []),
                              "perfil": contexto.get("perfil") or "sin datos",
                              "tramites": contexto.get("tramites") or "ninguno",
                              "recuerdos": contexto.get("recuerdos") or "ninguno", "consulta": consulta})

    return planificar_llm


def validar_plan(plan: PlanLLM, herramientas: dict, consulta: str, intencion: str) -> tuple:
    """El Manager revisa el plan del LLM antes de ejecutarlo. Devuelve (pasos válidos, observaciones)."""
    pasos, notas = [], []
    for p in plan.pasos[:MAX_PASOS_PLAN]:
        h = herramientas.get(p.herramienta)
        if h is None or p.herramienta in NO_PLANIFICABLES:
            notas.append(f"se descarta '{p.herramienta}': no es una herramienta permitida")
            continue
        args = {k: v for k, v in (p.argumentos or {}).items() if v not in (None, "")}
        try:
            h.args_schema.model_validate(args)
        except Exception:
            if p.herramienta in ("verificar_requisitos_practica",):  # sus datos se completan o se piden
                args = {}
            else:
                notas.append(f"se descarta '{p.herramienta}': argumentos inválidos")
                continue
        if p.herramienta == "redactar_solicitud" and not pide_documento(consulta):
            notas.append("se omite redactar_solicitud: el estudiante no pidió un documento")
            continue
        pasos.append({**paso(p.herramienta, p.objetivo), "args": args})
    if pasos and intencion in TRAMITES and not any(p["herramienta"] == "guardar_tramite" for p in pasos):
        etapa = "entregar_solicitud" if any(p["herramienta"] == "redactar_solicitud" for p in pasos) \
            else "reunir_documentos"
        pasos.append(paso("guardar_tramite", "recordar la etapa para otra sesión", tramite=intencion, etapa=etapa))
        notas.append("se agrega guardar_tramite: un trámite prolongado debe quedar en memoria")
    return pasos, notas


def planificar(consulta: str, intencion: str, contexto: dict, herramientas: dict,
               planificador_llm: Optional[Callable] = None) -> dict:
    """Devuelve {objetivo, pasos, metodo, notas}. Las intenciones críticas siempre van por reglas."""
    reglas = {"objetivo": _OBJETIVOS[intencion], "notas": [],
              "pasos": planificar_por_reglas(consulta, intencion, contexto.get("datos"))}
    if planificador_llm is None or intencion in ("olvidar", "excepcional"):
        return {**reglas, "metodo": "reglas" if planificador_llm else "reglas (sin LLM)"}
    try:
        plan = planificador_llm(consulta, contexto)
        pasos, notas = validar_plan(plan, herramientas, consulta, intencion) if plan else ([], [])
    except Exception as e:  # sin red, cuota agotada, salida malformada
        return {**reglas, "metodo": f"reglas (el LLM falló: {type(e).__name__})"}
    if not pasos:
        return {**reglas, "metodo": "reglas (plan del LLM vacío o inválido)", "notas": notas}
    return {"objetivo": plan.objetivo or reglas["objetivo"], "pasos": pasos, "metodo": "LLM (function calling)",
            "notas": notas}


# ====================================================== validación del Manager
def siguiente_pendiente(plan: list, desde: int = 0) -> Optional[int]:
    return next((i for i in range(desde, len(plan)) if plan[i]["estado"] == "pendiente"), None)


def _omitir(plan: list, desde: int, herramientas: tuple, motivo: str) -> list:
    omitidos = []
    for p in plan[desde:]:
        if p["herramienta"] in herramientas and p["estado"] == "pendiente":
            p["estado"], p["motivo"] = "omitido", motivo
            omitidos.append(p["herramienta"])
    return omitidos


def _fijar_etapa(plan: list, desde: int, etapa: str, proximo: str = "") -> bool:
    for p in plan[desde:]:
        if p["herramienta"] == "guardar_tramite" and p["estado"] == "pendiente":
            p["args"].update(etapa=etapa, proximo_paso=proximo or ETAPAS.get(etapa, ""))
            return True
    return False


def _agregar(plan: list, nuevo: dict, despues_de: Optional[int] = None) -> None:
    """Inserta un paso después de 'despues_de' o, si es None, al final del plan."""
    plan.insert(len(plan) if despues_de is None else despues_de + 1, {**nuevo, "agregado": True})


def evaluar_paso(plan: list, i: int, resultado: dict, intentos: int, replanes: int, iteraciones: int,
                 consulta: str, area: str = "otro") -> dict:
    """Valida el resultado del paso i. Acciones: continuar | reintentar | pedir_dato | finalizar."""
    plan = copy.deepcopy(plan)
    h = plan[i]["herramienta"]
    replanificable = replanes < MAX_REPLANES

    def salida(accion, motivo, replan=False, falta=None):
        nxt = i if accion == "reintentar" else siguiente_pendiente(plan, i + 1)
        if accion == "continuar" and (nxt is None or iteraciones >= MAX_ITERACIONES):
            if nxt is not None:
                motivo += f" · se alcanzó el máximo de {MAX_ITERACIONES} herramientas por turno"
            accion = "finalizar"
        return {"accion": accion, "plan": plan, "siguiente": nxt, "motivo": motivo, "replan": replan, "falta": falta}

    # 1) Falla técnica: un reintento; si persiste, se cancela lo pendiente y se deriva
    if resultado.get("error"):
        if intentos < 2:
            plan[i]["estado"] = "pendiente"
            return salida("reintentar", f"{h} falló ({resultado['error']}): el Manager pide repetir el paso")
        if replanificable and h != "registrar_derivacion":
            _omitir(plan, i + 1, tuple(AGENTE_DE), "se cancela porque una herramienta previa falló")
            _agregar(plan, paso("registrar_derivacion", "derivar porque una herramienta no respondió",
                                area=area if area != "otro" else "academico", resumen=consulta), i)
            return salida("continuar", f"{h} falló dos veces: se replanifica para derivar con un ticket", replan=True)
        return salida("continuar", f"{h} falló: se continúa con lo disponible")

    # 2) Falta un dato que solo el estudiante conoce: se pausa el plan (queda en la memoria de corto plazo)
    if resultado.get("falta"):
        plan[i]["estado"] = "pendiente"
        return {"accion": "pedir_dato", "plan": plan, "siguiente": i, "falta": resultado["falta"], "replan": False,
                "motivo": f"{h} necesita '{resultado['falta']}': se pausa el plan y se pregunta al estudiante"}

    if not replanificable:
        return salida("continuar", f"{h} completado (sin replanificar: se alcanzó el máximo de {MAX_REPLANES})")

    # 3) Sin evidencia en los documentos: no se redacta nada sin respaldo y se deriva
    if h == "buscar_normativa" and resultado.get("sin_evidencia"):
        _omitir(plan, i + 1, ("redactar_solicitud",), "no hay evidencia documental que la respalde")
        _fijar_etapa(plan, i + 1, "derivado")
        if not any(p["herramienta"] == "registrar_derivacion" for p in plan):
            _agregar(plan, paso("registrar_derivacion", "derivar porque los documentos no responden",
                                area=resultado.get("area") if resultado.get("area") in
                                ("academico", "administrativo", "practica_titulacion", "ti") else "academico",
                                resumen=consulta), i)
        return salida("continuar", "los documentos no responden: se replanifica para derivar con un ticket en vez "
                                   "de responder sin fuente", replan=True)

    # 4) Resultados de razonamiento que cambian el curso del plan
    if h == "verificar_requisitos_practica":
        if resultado.get("cumple") is False:
            omitidos = _omitir(plan, i + 1, ("consultar_calendario", "redactar_solicitud"),
                               "no aplica hasta cumplir el avance de malla")
            _fijar_etapa(plan, i + 1, "cumplir_requisitos",
                         f"Aprobar asignaturas hasta llegar al {resultado.get('avance_minimo')} % de la malla")
            detalle = f"se omite {' y '.join(omitidos)}; " if omitidos else ""
            return salida("continuar", f"no cumple el avance de malla: {detalle}la etapa pasa a 'cumplir "
                                       "requisitos'", replan=True)
        if resultado.get("gestion_individual") is False:
            _omitir(plan, i + 1, ("buscar_normativa", "consultar_calendario", "redactar_solicitud"),
                    "en esta carrera la práctica la asigna la carrera")
            _fijar_etapa(plan, i + 1, "coordinar_campo_clinico")
            return salida("continuar", "la carrera asigna los campos clínicos: se omite la inscripción individual",
                          replan=True)
    if h == "consultar_calendario" and resultado.get("estado") in ("cerrado", "proximo"):
        omitidos = _omitir(plan, i + 1, ("redactar_solicitud",), f"el período está {resultado['estado']}")
        proximo = (f"La inscripción abre el {resultado['inicio'][8:10]}-{resultado['inicio'][5:7]}: vuelve a "
                   "revisarlo ese día" if resultado["estado"] == "proximo"
                   else "El período ya cerró: revisa las fechas del próximo semestre con tu sede")
        cambio = _fijar_etapa(plan, i + 1, "esperar_apertura", proximo)
        if omitidos or cambio:
            return salida("continuar", f"el período '{resultado['evento']}' está {resultado['estado']}: "
                                       "no se redacta la solicitud y la etapa pasa a 'esperar apertura'", replan=True)
    if h in ("calcular_asistencia", "calcular_nota_necesaria") and \
            (resultado.get("cumple") is False or resultado.get("alcanzable") is False):
        if not any("repruebo" in str(p["args"].get("pregunta", "")) for p in plan):
            _agregar(plan, paso("buscar_normativa", "explicar qué pasa si reprueba",
                                pregunta="¿Qué pasa si repruebo una asignatura?", area="academico"))
            return salida("continuar", "el cálculo indica riesgo de reprobar: se agrega un paso para explicar "
                                       "las consecuencias según el reglamento", replan=True)

    return salida("continuar", f"{h} completado")
