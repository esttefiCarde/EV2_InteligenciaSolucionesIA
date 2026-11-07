"""Herramientas del agente (EP2, IE1-IE2): consulta, razonamiento y escritura.

Diseño de herramientas según las buenas prácticas de LangChain (clase 2.3.1): una función por
herramienta, descripción clara (es lo que lee el LLM para decidir por function calling) y argumentos
tipados con Pydantic (JSON Schema). Las herramientas se reparten entre tres agentes ejecutores, y
cada uno recibe solo las que necesita.

Cada herramienta devuelve un dict:
  mensaje         texto para el estudiante, con citas [n]
  fuentes         fuentes citadas (las arma el código, no el LLM)
  falta           dato que solo el estudiante puede entregar: el Manager pausa el plan y lo pide
  sin_evidencia   los documentos no responden: el Manager replanifica para derivar
  error           falla técnica: el Manager reintenta o deriva
"""
import functools
import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, Literal, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from . import razonamiento as rz
from .config import CONTACTOS, SALIDAS_DIR
from .extraccion import normalizar_carrera
from .guardrails import enmascarar
from .memoria import MemoriaAgente, anonimizar

Area = Literal["academico", "administrativo", "practica_titulacion", "ti"]
Evento = Literal["inscripcion_practica", "inscripcion_titulacion", "retiro_asignaturas", "suspension_estudios",
                 "examenes_finales"]
TipoSolicitud = Literal["inscripcion_practica", "inscripcion_titulacion", "justificacion_inasistencia",
                        "suspension_estudios", "retiro_asignaturas"]
Tramite = Literal["practica", "titulacion", "suspension", "retiro", "justificacion"]

NOMBRE_TRAMITE = {"practica": "Práctica profesional", "titulacion": "Titulación", "suspension": "Suspensión de estudios",
                  "retiro": "Retiro de asignaturas", "justificacion": "Justificación de inasistencia"}
def etapa_legible(etapa: str) -> str:
    return {"coordinar_campo_clinico": "coordinar campo clínico"}.get(etapa, etapa.replace("_", " "))


ETAPAS = {
    "reunir_documentos": "Reunir los documentos y pedir la carta de presentación a tu coordinación",
    "entregar_solicitud": "Completar el borrador con tus datos y entregarlo a la coordinación",
    "cumplir_requisitos": "Aprobar asignaturas hasta alcanzar el avance de malla mínimo",
    "esperar_apertura": "Esperar que abra el período de inscripción y volver a revisarlo",
    "coordinar_campo_clinico": "Coordinar con tu carrera la asignación del campo clínico",
    "derivado": "Esperar la respuesta de la unidad a la que se derivó tu caso",
}

# Equipo de agentes ejecutores (rol, objetivo y herramientas). El Manager no tiene herramientas: delega.
AGENTES_EJECUTORES = {
    "consulta": {"rol": "Agente de Consulta",
                 "objetivo": "Obtener información verificable desde los documentos, el calendario y la memoria",
                 "herramientas": ["buscar_normativa", "consultar_calendario", "consultar_mis_tramites"]},
    "razonamiento": {"rol": "Agente de Razonamiento",
                     "objetivo": "Calcular y comparar datos del estudiante con las reglas académicas",
                     "herramientas": ["verificar_requisitos_practica", "calcular_asistencia",
                                      "calcular_nota_necesaria"]},
    "escritura": {"rol": "Agente de Escritura",
                  "objetivo": "Producir borradores y registros que dejan constancia del trámite",
                  "herramientas": ["redactar_solicitud", "registrar_derivacion", "guardar_tramite",
                                   "olvidar_mis_datos"]},
}
AGENTE_DE = {h: a for a, d in AGENTES_EJECUTORES.items() for h in d["herramientas"]}
# olvidar_mis_datos es una acción crítica: solo la invoca la política del Manager, nunca el LLM
NO_PLANIFICABLES = {"olvidar_mis_datos"}
# En la estrategia reactiva (ReAct) solo se usan herramientas sin efectos secundarios
REACTIVAS = AGENTES_EJECUTORES["consulta"]["herramientas"] + AGENTES_EJECUTORES["razonamiento"]["herramientas"]


@dataclass
class Contexto:
    """Lo que las herramientas necesitan del turno actual."""
    usuario: str
    memoria: MemoriaAgente
    consultar_rag: Callable          # AsistenteDuoc.consultar(pregunta, carrera, area) del EP1
    fecha: Callable[[], date] = rz.hoy
    salidas: Path = SALIDAS_DIR
    perfil: dict = field(default_factory=dict)
    datos_turno: dict = field(default_factory=dict)   # p. ej. avance de malla: se usa y no se guarda
    fuentes: list = field(default_factory=list)       # fuentes citadas en el turno (numeración única)
    archivos: list = field(default_factory=list)


# ------------------------------------------------------------------ esquemas
class ArgsBuscar(BaseModel):
    pregunta: str = Field(description="Pregunta autocontenida sobre normativa o procedimientos de Duoc UC")
    area: Optional[Area] = Field(None, description="Área del tema, si se conoce")


class ArgsCalendario(BaseModel):
    evento: Evento = Field(description="Período del calendario académico que se quiere consultar")


class ArgsVacio(BaseModel):
    pass


class ArgsRequisitos(BaseModel):
    carrera: Optional[str] = Field(None, description="Carrera del estudiante; omitir si no se conoce")
    avance_malla: Optional[float] = Field(None, ge=0, le=100,
                                          description="Porcentaje de la malla aprobado; omitir si el estudiante no lo dijo")


class ArgsAsistencia(BaseModel):
    clases_totales: int = Field(gt=0, description="Total de clases de la asignatura")
    inasistencias: int = Field(ge=0, description="Clases a las que faltó")
    tipo: Literal["teorica", "practica"] = Field("teorica", description="practica = taller o laboratorio")


class NotaPonderada(BaseModel):
    nota: float = Field(ge=1, le=7, description="Nota de 1,0 a 7,0")
    ponderacion: float = Field(gt=0, le=100, description="Porcentaje de la nota final que vale esa evaluación")


class ArgsNotas(BaseModel):
    notas: list[NotaPonderada] = Field(min_length=1, description="Notas ya obtenidas con su ponderación")


class ArgsSolicitud(BaseModel):
    tipo: TipoSolicitud = Field(description="Tipo de solicitud que se redacta")
    motivo: str = Field("", description="Motivo breve, sin datos personales")


class ArgsTicket(BaseModel):
    area: Literal["academico", "administrativo", "practica_titulacion", "ti", "otro"]
    resumen: str = Field(description="Resumen del caso sin datos personales")


class ArgsTramite(BaseModel):
    tramite: Tramite
    etapa: str = Field(description="Etapa actual: " + ", ".join(ETAPAS))
    proximo_paso: str = Field("", description="Qué debe hacer el estudiante a continuación")


# -------------------------------------------------------------------- apoyo
def _seguro(f):
    """Una falla de la herramienta se informa al Manager en vez de interrumpir el turno."""
    @functools.wraps(f)
    def envoltura(*a, **kw):
        try:
            return f(*a, **kw)
        except Exception as e:
            return {"error": f"{type(e).__name__}: {str(e)[:150]}"}
    return envoltura


def _clave_fuente(etiqueta: str) -> str:
    """'Doc – Sección (interno, v2026.1)' y 'Doc – Sección' son la misma fuente."""
    return re.sub(r"\s*\([^()]*\)$", "", etiqueta).strip()


def _numero_fuente(ctx: Contexto, etiqueta: str) -> int:
    """Número único de una fuente dentro del turno (si ya se citó, se reutiliza)."""
    for i, f in enumerate(ctx.fuentes, 1):
        anterior = f.split("] ", 1)[1]
        if _clave_fuente(anterior) == _clave_fuente(etiqueta):
            if len(etiqueta) > len(anterior):  # se conserva la etiqueta más completa
                ctx.fuentes[i - 1] = f"[{i}] {etiqueta}"
            return i
    ctx.fuentes.append(f"[{len(ctx.fuentes) + 1}] {etiqueta}")
    return len(ctx.fuentes)


def _citar(ctx: Contexto, r: dict) -> dict:
    if r.get("fuente") and r.get("mensaje"):
        n = _numero_fuente(ctx, r["fuente"])
        r["mensaje"] += f" [{n}]"
        r["fuentes"] = [ctx.fuentes[n - 1]]
    return r


def _renumerar(ctx: Contexto, texto: str, fuentes: list) -> tuple:
    """Pasa las citas [k] de una respuesta del RAG a la numeración única del turno."""
    mapa = {}
    for f in fuentes:
        m = re.match(r"\[(\d+)\]\s*(.*)", f)
        if m:
            mapa[int(m.group(1))] = _numero_fuente(ctx, m.group(2))
    texto = re.sub(r"\[(\d+)\]", lambda m: f"[{mapa.get(int(m.group(1)), m.group(1))}]", texto)
    return texto, [ctx.fuentes[n - 1] for n in sorted(set(mapa.values()))]


def _carpeta(ctx: Contexto) -> Path:
    return ctx.salidas / re.sub(r"[^\w-]", "_", ctx.usuario)[:40]


_PLANTILLAS = {
    "inscripcion_practica": ("Solicitud de inscripción de práctica profesional", "Coordinación de Práctica",
                             "Solicito inscribir mi práctica profesional en el período vigente. Declaro haber "
                             "verificado que cumplo el avance de malla que exige mi carrera.",
                             "carta de presentación de la coordinación; ficha de inscripción de práctica; "
                             "comprobante del seguro; carta de aceptación firmada por la empresa"),
    "inscripcion_titulacion": ("Solicitud de inscripción al proceso de titulación", "Coordinación de Titulación",
                               "Solicito iniciar el proceso de titulación en la modalidad que corresponde a mi "
                               "carrera.", "formulario de inscripción de titulación; certificado de aprobación de "
                               "práctica; certificado de concentración de notas; comprobante de pago de derechos"),
    "justificacion_inasistencia": ("Justificación de inasistencia a evaluación", "Coordinación de carrera",
                                   "Solicito justificar mi inasistencia a la evaluación de la asignatura "
                                   "[ASIGNATURA] del día [FECHA] y que se fije una nueva fecha para rendirla.",
                                   "certificado médico u otro antecedente que respalde la ausencia"),
    "suspension_estudios": ("Solicitud de suspensión de estudios", "Punto Estudiantil",
                            "Solicito suspender mis estudios por [1 o 2] semestre(s), dentro del máximo de dos "
                            "semestres que permite la normativa.", "antecedentes que respalden la solicitud"),
    "retiro_asignaturas": ("Solicitud de retiro de asignatura", "Punto Estudiantil",
                           "Solicito el retiro de la asignatura [ASIGNATURA] dentro del período que fija el "
                           "calendario académico.", "no requiere documentos adicionales"),
}


# ================================================================ herramientas
def crear_herramientas(ctx: Contexto) -> dict:
    """Crea las herramientas ligadas al contexto del turno. Devuelve {nombre: StructuredTool}."""

    # ------------------------------------------------------------ consulta
    @_seguro
    def buscar_normativa(pregunta: str, area: Optional[str] = None) -> dict:
        r = ctx.consultar_rag(pregunta, ctx.perfil.get("carrera"), area)
        if r.pide_aclaracion:
            return {"falta": "carrera", "area": r.area}
        if r.derivado:
            return {"sin_evidencia": True, "motivo": r.motivo_derivacion, "area": r.area, "mensaje": r.texto}
        texto, fuentes = _renumerar(ctx, r.texto, r.fuentes)
        return {"mensaje": texto, "fuentes": fuentes, "area": r.area}

    @_seguro
    def consultar_calendario(evento: str) -> dict:
        return _citar(ctx, rz.estado_periodo(evento, ctx.fecha()))

    @_seguro
    def consultar_mis_tramites() -> dict:
        tramites, tickets = ctx.memoria.tramites(ctx.usuario), ctx.memoria.tickets(ctx.usuario)
        if not tramites and not tickets:
            return {"vacio": True, "mensaje": "No tengo trámites ni tickets guardados a tu nombre."}
        lineas = [f"• **{NOMBRE_TRAMITE.get(t['tramite'], t['tramite'])}**: etapa *{etapa_legible(t['etapa'])}* "
                  f"(actualizado el {t['actualizado'][:10]}). Próximo paso: {t['proximo_paso']}." for t in tramites]
        lineas += [f"• Ticket **{t['id']}** ({t['estado']}, {t['ts'][:10]}): {t['resumen']}" for t in tickets]
        return {"tramites": tramites, "tickets": tickets,
                "mensaje": "Esto es lo que tengo registrado de tus trámites:\n" + "\n".join(lineas)}

    # -------------------------------------------------------- razonamiento
    @_seguro
    def verificar_requisitos_practica(carrera: Optional[str] = None, avance_malla: Optional[float] = None) -> dict:
        carrera = normalizar_carrera(carrera) or ctx.perfil.get("carrera")
        if not carrera:
            return {"falta": "carrera"}
        regla = rz.reglas()["practica"]["carreras"].get(carrera)
        avance = avance_malla if avance_malla is not None else ctx.datos_turno.get("avance_malla")
        if regla and regla["gestion_individual"] and avance is None:
            return {"falta": "avance_malla", "carrera": carrera}
        return _citar(ctx, rz.evaluar_requisitos_practica(carrera, avance or 0))

    @_seguro
    def calcular_asistencia(clases_totales: int, inasistencias: int, tipo: str = "teorica") -> dict:
        return _citar(ctx, rz.calcular_asistencia(clases_totales, inasistencias, tipo))

    @_seguro
    def calcular_nota_necesaria(notas: list) -> dict:
        notas = [n.model_dump() if hasattr(n, "model_dump") else dict(n) for n in notas]
        return _citar(ctx, rz.calcular_nota_necesaria(notas))

    # ------------------------------------------------------------ escritura
    @_seguro
    def redactar_solicitud(tipo: str, motivo: str = "") -> dict:
        carrera = ctx.perfil.get("carrera")
        if tipo in ("inscripcion_practica", "inscripcion_titulacion") and not carrera:
            return {"falta": "carrera"}
        titulo, destino, cuerpo, adjuntos = _PLANTILLAS[tipo]
        hoy = ctx.fecha()
        texto = "\n".join([
            f"# {titulo}", "", f"**Para:** {destino}{' – ' + carrera if carrera else ''}",
            f"**Fecha:** {hoy:%d-%m-%Y}", "", "**Nombre:** [NOMBRE COMPLETO]  ", "**RUT:** [RUT]  ",
            f"**Carrera:** {carrera or '[CARRERA]'}  ", "**Sede y jornada:** [SEDE] · [JORNADA]", "",
            cuerpo + (f" Motivo: {enmascarar(motivo)}." if motivo else ""), "",
            f"**Documentos que adjunto:** {adjuntos}.", "", "Atentamente,", "", "[FIRMA]", "", "---",
            "*Borrador generado por el Asistente Duoc UC (proyecto académico). Completa tus datos personales a "
            "mano: el asistente no los pide ni los guarda.*"])
        ruta = _carpeta(ctx) / f"{tipo}_{hoy:%Y%m%d}.md"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(texto, encoding="utf-8")
        ctx.archivos.append(str(ruta))
        return {"archivo": str(ruta), "mensaje": f"📝 Preparé un borrador de **{titulo.lower()}** "
                f"(`{ruta.name}`). Complétalo con tus datos personales antes de entregarlo."}

    @_seguro
    def registrar_derivacion(area: str, resumen: str) -> dict:
        ticket = ctx.memoria.crear_ticket(ctx.usuario, area, resumen)
        ctx.salidas.mkdir(parents=True, exist_ok=True)
        with open(ctx.salidas / "tickets.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": ticket, "area": area, "resumen": anonimizar(resumen),
                                "fecha": ctx.fecha().isoformat()}, ensure_ascii=False) + "\n")
        return {"ticket": ticket, "derivado": True,
                "mensaje": f"🎫 Registré tu caso con el código **{ticket}** para "
                           f"{CONTACTOS.get(area, CONTACTOS['otro'])}. Una persona lo revisará y puedes "
                           "preguntarme por él cuando quieras."}

    @_seguro
    def guardar_tramite(tramite: str, etapa: str, proximo_paso: str = "") -> dict:
        proximo = proximo_paso or ETAPAS.get(etapa, "")
        ctx.memoria.guardar_tramite(ctx.usuario, tramite, etapa, proximo)
        return {"guardado": True, "tramite": tramite, "etapa": etapa,
                "mensaje": f"🗂️ Guardé tu avance en **{NOMBRE_TRAMITE.get(tramite, tramite).lower()}**: etapa "
                           f"*{etapa_legible(etapa)}*. Próximo paso: {proximo}. Puedes retomarlo en otra sesión."}

    @_seguro
    def olvidar_mis_datos() -> dict:
        borrados = ctx.memoria.olvidar(ctx.usuario)
        carpeta = _carpeta(ctx)
        if carpeta.exists():
            for archivo in carpeta.glob("*.md"):
                archivo.unlink()
        return {"borrados": borrados, "mensaje": "🧹 Listo: borré tu perfil, tus trámites, tus tickets, tus "
                "conversaciones y tus borradores. Desde ahora no recuerdo nada de ti."}

    definiciones = [
        (buscar_normativa, ArgsBuscar, "Busca en los reglamentos y documentos oficiales de Duoc UC (RAG con "
         "agentes especialistas por área) y responde con citas. Úsala para todo requisito, plazo, documento o "
         "procedimiento. No inventa: si no hay evidencia lo indica."),
        (consultar_calendario, ArgsCalendario, "Indica si un período del calendario académico (inscripción de "
         "práctica o de titulación, retiro de asignaturas, suspensión de estudios, exámenes) está abierto, "
         "próximo o cerrado en la fecha actual."),
        (consultar_mis_tramites, ArgsVacio, "Lee de la memoria de largo plazo los trámites en curso del "
         "estudiante, su etapa y sus tickets. Úsala cuando pregunte en qué quedó o qué le falta."),
        (verificar_requisitos_practica, ArgsRequisitos, "Compara el porcentaje de malla aprobado con el mínimo "
         "que exige la carrera para iniciar la práctica profesional."),
        (calcular_asistencia, ArgsAsistencia, "Calcula el porcentaje de asistencia de una asignatura, si cumple "
         "el mínimo y cuántas clases más puede faltar."),
        (calcular_nota_necesaria, ArgsNotas, "Calcula la nota mínima que necesita en lo que resta de la "
         "asignatura para aprobar con 4,0."),
        (redactar_solicitud, ArgsSolicitud, "Escribe un borrador de solicitud en Markdown, sin datos personales. "
         "Úsala solo si el estudiante pide preparar o redactar el documento."),
        (registrar_derivacion, ArgsTicket, "Registra un ticket para que una persona atienda el caso. Úsala en "
         "casos excepcionales o cuando los documentos no responden."),
        (guardar_tramite, ArgsTramite, "Guarda en la memoria de largo plazo la etapa de un trámite prolongado "
         "(práctica, titulación…) para retomarlo en otra sesión."),
        (olvidar_mis_datos, ArgsVacio, "Borra toda la memoria del estudiante (derecho de supresión)."),
    ]
    return {f.__name__: StructuredTool.from_function(func=f, name=f.__name__, description=d, args_schema=s)
            for f, s, d in definiciones}
