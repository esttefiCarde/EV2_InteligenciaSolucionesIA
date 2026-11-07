"""Agente del asistente Duoc UC (EP2): orquestación jerárquica con un Agente Manager (clase 2.3.1).

    Estudiante → guardrails → recordar (memoria) → Manager elige la estrategia
        ├─ directa:     política del Manager (caso excepcional, borrar datos)
        ├─ reactiva:    ReAct con function calling (AgentExecutor de LangChain) para consultas puntuales
        └─ planificada: Plan-and-Execute. El Manager arma el plan, delega cada paso en un agente
                        ejecutor (Consulta, Razonamiento o Escritura) y valida el resultado antes de
                        seguir: continúa, reintenta, pausa para pedir un dato o replanifica.
    → síntesis (respuesta + fuentes armadas por código) → memorizar → respuesta + traza

El estado del flujo (plan, paso actual, resultados y datos del turno) vive en este objeto mientras dura
el turno; si el plan se pausa, se guarda en la memoria de corto plazo y se reanuda en el turno siguiente.
"""
import json
import time
from datetime import date
from typing import Callable, Optional

from . import derivacion, guardrails, logger_uso, planificador as pl, razonamiento as rz, router
from .config import AGENTE_LOG_PATH, CONTACTOS, MAX_ITERACIONES_REACT, SALIDAS_DIR
from .extraccion import extraer_perfil, extraer_porcentaje, normalizar_carrera, numero_suelto
from .herramientas import AGENTES_EJECUTORES, NOMBRE_TRAMITE, REACTIVAS, Contexto, crear_herramientas, etapa_legible
from .llm import CONTADOR
from .memoria import MemoriaAgente, contextualizar
from .modelos import RespuestaAgente
from .pipeline import _es_saludo

SALUDO = ("¡Hola! Soy el asistente para estudiantes de Duoc UC. Puedo responder dudas con los reglamentos, "
          "calcular tu asistencia o la nota que necesitas, revisar si cumples los requisitos de práctica, "
          "preparar borradores de solicitudes y recordar en qué va tu trámite. ¿Qué necesitas?")
PREGUNTAS_DATO = {
    "carrera": "Para seguir necesito saber **de qué carrera eres**, porque los requisitos cambian según la "
               "carrera. ¿Cuál es tu carrera?",
    "avance_malla": "¿Qué **porcentaje de tu malla** llevas aprobado? Lo uso solo para este cálculo y no lo guardo.",
}
ROL = {a: d["rol"] for a, d in AGENTES_EJECUTORES.items()}


def _resumen(r: dict) -> str:
    """Observación breve de una herramienta para la traza."""
    if not isinstance(r, dict):
        return str(r)[:180]
    if r.get("error"):
        return f"❌ error: {r['error']}"
    if r.get("falta"):
        return f"falta el dato '{r['falta']}'"
    if r.get("sin_evidencia"):
        return f"sin evidencia en los documentos ({r.get('motivo', '')})"
    claves = [f"{k}={r[k]}" for k in ("estado", "cumple", "gestion_individual", "alcanzable", "ticket", "etapa")
              if k in r and r[k] is not None]
    texto = " ".join(str(r.get("mensaje", "")).replace("**", "").split())
    return (" · ".join(claves) + " · " if claves else "") + (texto[:160] + ("…" if len(texto) > 160 else ""))


class AgenteDuoc:
    def __init__(self, rag: Callable, memoria: MemoriaAgente, chat_llm=None, chat_manager=None,
                 salidas=SALIDAS_DIR, registrar: bool = True):
        self.rag = rag                     # AsistenteDuoc.consultar (pipeline RAG multiagente del EP1)
        self.memoria = memoria
        self.chat = chat_llm               # LLM de los ejecutores (ReAct)
        self.salidas = salidas
        self.registrar = registrar
        manager = chat_manager or chat_llm
        catalogo = crear_herramientas(Contexto(usuario="catalogo", memoria=memoria, consultar_rag=rag))
        self.planificador_llm = pl.crear_planificador_llm(manager, catalogo) if manager is not None else None

    # ======================================================================= API
    def conversar(self, mensaje: str, usuario: str = "anonimo", sesion: str = "principal",
                  fecha: Optional[date] = None) -> RespuestaAgente:
        t0, llamadas0 = time.time(), CONTADOR.llamadas
        traza = []

        def nota(tipo, texto):
            traza.append({"tipo": tipo, "texto": texto})

        sensibles = guardrails.detectar_datos_sensibles(mensaje)
        consulta = guardrails.enmascarar(mensaje).strip()  # desde aquí nada ve el RUT ni el correo
        if sensibles:
            nota("guardrail", f"datos personales enmascarados antes de procesar: {', '.join(sensibles)}")
        r = self._bloqueos(consulta, nota)
        if r is None:
            r = self._atender(consulta, usuario, sesion, fecha, nota)
        if sensibles:
            r.texto = ("⚠️ Por tu privacidad, no necesito tu RUT ni datos personales; ya los oculté de tu consulta "
                       "y no los guardo.\n\n") + r.texto
        r.traza, r.datos_sensibles = traza, sensibles
        r.perfil, r.tramites = self.memoria.perfil(usuario), self.memoria.tramites(usuario)
        r.llamadas_llm = CONTADOR.llamadas - llamadas0
        r.latencia_ms = int((time.time() - t0) * 1000)
        self._registrar(consulta, r)
        return r

    # =================================================================== etapas
    def _bloqueos(self, consulta: str, nota) -> Optional[RespuestaAgente]:
        """Guardrails del EP1: estos casos no llegan al Manager ni a las herramientas."""
        if guardrails.detectar_inyeccion(consulta):
            nota("guardrail", "posible inyección de instrucciones: se bloquea sin usar herramientas")
            return RespuestaAgente(texto=derivacion.construir_mensaje("inyeccion", "otro", consulta),
                                   intencion="inyeccion", estrategia="bloqueada")
        if guardrails.es_caso_sensible(consulta):
            area = router.clasificar_por_palabras(consulta)[0]
            nota("guardrail", "tema delicado: se deriva de inmediato a una persona y no se guarda el contenido")
            return RespuestaAgente(texto=derivacion.construir_mensaje("sensible", area, consulta), intencion="sensible",
                                   estrategia="bloqueada", derivado=True)
        return None

    def _atender(self, consulta: str, usuario: str, sesion: str, fecha: Optional[date], nota) -> RespuestaAgente:
        mem = self.memoria
        estado = mem.estado(usuario, sesion)
        nueva_sesion = mem.n_mensajes(usuario, sesion) == 0
        ctx = Contexto(usuario=usuario, memoria=mem, consultar_rag=self.rag, salidas=self.salidas,
                       fecha=(lambda: fecha) if fecha else rz.hoy, perfil=mem.perfil(usuario))

        if _es_saludo(consulta):  # un saludo no descarta un plan pausado
            r = RespuestaAgente(texto=SALUDO, intencion="saludo", estrategia="directa")
            r.texto += self._recordatorio(mem.tramites(usuario), nueva_sesion, "saludo")
            mem.guardar_turno(usuario, sesion, consulta, r.texto)
            return r

        # ---------------------------------------------- recordar (memoria)
        pendiente = estado.get("pendiente")
        declarado = extraer_perfil(consulta)
        if pendiente and pendiente["falta"] == "carrera" and not declarado.get("carrera"):
            if normalizar_carrera(consulta):
                declarado["carrera"] = normalizar_carrera(consulta)
        if declarado:
            anterior = ctx.perfil.get("carrera")
            if declarado.get("carrera") and anterior and declarado["carrera"] != anterior:
                nota("decision", f"condición cambiante: la carrera cambió de {anterior} a {declarado['carrera']}; "
                                 "los pasos siguientes usan la nueva")
            ctx.perfil = mem.actualizar_perfil(usuario, **declarado)
            nota("memoria", "largo plazo: perfil actualizado (" + ", ".join(f"{k}={v}" for k, v in declarado.items()) + ")")
        avance = extraer_porcentaje(consulta)
        if avance is not None and any(c in guardrails.normalizar(consulta) for c in ("malla", "avance", "llevo", "aprob")):
            ctx.datos_turno["avance_malla"] = avance

        reanudar = False
        if pendiente:
            if pendiente["falta"] == "carrera":
                reanudar = bool(declarado.get("carrera"))
            elif pendiente["falta"] == "avance_malla":
                valor = ctx.datos_turno.get("avance_malla", extraer_porcentaje(consulta) or numero_suelto(consulta))
                if valor is not None:
                    ctx.datos_turno["avance_malla"], reanudar = valor, True
            if reanudar:
                nota("memoria", f"corto plazo: el estudiante entregó '{pendiente['falta']}'; se reanuda el plan "
                                f"pausado en el paso {pendiente['paso'] + 1}")
            else:
                nota("decision", "el estudiante cambió de tema: se descarta el plan pausado")

        consulta_efectiva = consulta
        if not reanudar and self.chat is None and pl.detectar_intencion(consulta) == "consulta":
            consulta_efectiva = contextualizar(consulta, estado.get("tema"))
            if consulta_efectiva != consulta:
                nota("memoria", f"corto plazo: pregunta de seguimiento completada con el tema anterior → "
                                f"«{consulta_efectiva}»")
        ventana = mem.ventana(usuario, sesion)
        if ventana:
            nota("memoria", f"corto plazo: ventana de {len(ventana)} mensaje(s) (ConversationBufferWindowMemory, "
                            f"k={mem.k} turnos)")
        recuerdos = mem.recordar(usuario, consulta_efectiva)
        if recuerdos:
            nota("memoria", f"largo plazo: {len(recuerdos)} consulta(s) anterior(es) parecida(s); la más cercana del "
                            f"{recuerdos[0]['fecha']} (similitud {recuerdos[0]['similitud']})")
        tramites = mem.tramites(usuario)

        # --------------------------------------------- Manager: estrategia
        herramientas = crear_herramientas(ctx)
        r = RespuestaAgente(texto="", recuerdos=recuerdos)
        if reanudar:
            r.intencion, r.objetivo, r.metodo_plan = pendiente["intencion"], pendiente["objetivo"], "reanudado"
            r.estrategia, r.motivo_estrategia = "planificada", "se reanuda el plan que quedó pausado"
            plan, consulta_efectiva = pendiente["plan"], pendiente["consulta"]
        else:
            r.intencion = pl.detectar_intencion(consulta_efectiva)
            r.estrategia, r.motivo_estrategia = pl.elegir_estrategia(r.intencion)
            plan = None
        nota("pensamiento", f"Manager · estrategia {r.estrategia}: {r.motivo_estrategia}")

        resultado = None
        if r.estrategia == "reactiva" and self.chat is not None:
            resultado = self._reactiva(consulta_efectiva, ctx, herramientas, ventana, nota)
            if resultado is not None:
                r.metodo_plan = "ReAct (AgentExecutor)"
        if resultado is None:
            if plan is None:
                contexto = {"ventana": ventana, "perfil": ctx.perfil, "datos": ctx.datos_turno,
                            "tramites": "; ".join(f"{t['tramite']}: {t['etapa']}" for t in tramites),
                            "recuerdos": "; ".join(e["texto"] for e in recuerdos)}
                planificador_llm = self.planificador_llm if r.estrategia == "planificada" else None
                p = pl.planificar(consulta_efectiva, r.intencion, contexto, herramientas, planificador_llm)
                plan, r.objetivo = p["pasos"], p["objetivo"]
                r.metodo_plan = r.metodo_plan or p["metodo"]
                for n in p["notas"]:
                    nota("decision", f"Manager valida el plan del LLM: {n}")
                nota("pensamiento", f"objetivo: {r.objetivo} · plan ({r.metodo_plan}): "
                                    + " → ".join(f"{x['herramienta']}" for x in plan))
            resultado = self._ejecutar_plan(plan, consulta_efectiva, ctx, herramientas, nota)

        r.plan, r.replanes = resultado["plan"], resultado.get("replanes", 0)
        r.herramientas = [o["herramienta"] for o in resultado["observaciones"]]
        r.archivos = list(ctx.archivos)
        r.texto, r.fuentes = resultado.get("texto"), list(ctx.fuentes)
        if r.texto is None:
            r.texto = self._sintetizar(resultado["observaciones"], r.intencion)
        r.derivado = any(o["herramienta"] == "registrar_derivacion" and not o["resultado"].get("error")
                         for o in resultado["observaciones"])

        # ------------------------------------------------- pausa o memorizar
        tema = {"consulta": consulta_efectiva, "intencion": r.intencion}
        if consulta_efectiva != consulta and not reanudar:  # una pregunta de seguimiento conserva el tema
            tema = estado.get("tema")
        nuevo_estado = {"tema": tema, "pendiente": None}
        if resultado.get("falta"):
            r.esperando = resultado["falta"]
            r.texto = "\n\n".join(x for x in (r.texto, PREGUNTAS_DATO.get(r.esperando, "")) if x)
            nuevo_estado["pendiente"] = {"plan": r.plan, "paso": resultado["pausa_en"], "falta": r.esperando,
                                         "consulta": consulta_efectiva, "intencion": r.intencion, "objetivo": r.objetivo}
            nota("memoria", "corto plazo: el plan queda pausado hasta recibir el dato")
        if r.intencion == "olvidar":
            return r  # tras borrar la memoria no se vuelve a guardar nada de este turno
        tocados = {o["args"].get("tramite") for o in resultado["observaciones"] if isinstance(o["args"], dict)}
        r.texto += self._recordatorio(tramites, nueva_sesion, r.intencion, tocados)
        mem.guardar_estado(usuario, sesion, nuevo_estado)
        mem.guardar_turno(usuario, sesion, consulta, r.texto)
        if not r.esperando:
            etapas = [o["resultado"].get("etapa") for o in resultado["observaciones"] if o["resultado"].get("etapa")]
            mem.guardar_episodio(usuario, consulta_efectiva, (r.objetivo or r.intencion) +
                                 (f" (etapa: {etapas[-1]})" if etapas else ""), r.intencion)
        return r

    # ================================================== estrategia planificada
    def _completar_args(self, p: dict, herramienta, ctx: Contexto, consulta: str) -> dict:
        """El ejecutor completa los argumentos con la memoria y los datos del turno."""
        args = {k: v for k, v in p["args"].items() if v is not None}
        campos = herramienta.args_schema.model_fields
        if "avance_malla" in campos and "avance_malla" not in args and "avance_malla" in ctx.datos_turno:
            args["avance_malla"] = ctx.datos_turno["avance_malla"]
        if herramienta.name == "buscar_normativa":
            args.setdefault("pregunta", consulta)
        if herramienta.name == "registrar_derivacion":
            args.setdefault("area", "academico")
            args.setdefault("resumen", consulta)
        return args

    def _ejecutar_plan(self, plan: list, consulta: str, ctx: Contexto, herramientas: dict, nota) -> dict:
        plan = [dict(x, args=dict(x["args"])) for x in plan]
        i = pl.siguiente_pendiente(plan)
        intentos, replanes, iteraciones, area, observaciones = {}, 0, 0, "otro", []
        while i is not None:
            p = plan[i]
            herramienta = herramientas.get(p["herramienta"])
            nota("pensamiento", f"paso {i + 1} · {ROL.get(p['agente'], 'Ejecutor')}: {p['objetivo']}")
            args = self._completar_args(p, herramienta, ctx, consulta) if herramienta else dict(p["args"])
            nota("accion", f"{p['herramienta']}({', '.join(f'{k}={v!r}' for k, v in args.items())})")
            try:
                if herramienta is None:
                    raise KeyError(f"herramienta desconocida: {p['herramienta']}")
                resultado = herramienta.invoke(args)
            except Exception as e:  # argumentos inválidos u otra falla: la decide el Manager
                resultado = {"error": f"{type(e).__name__}: {str(e)[:150]}"}
            iteraciones += 1
            intentos[i] = intentos.get(i, 0) + 1
            p["estado"] = "fallido" if resultado.get("error") else "ok"
            if p["herramienta"] == "buscar_normativa" and resultado.get("area") in CONTACTOS:
                area = resultado["area"]
            observaciones.append({"paso": i, "herramienta": p["herramienta"], "agente": p["agente"], "args": args,
                                  "resultado": resultado})
            nota("observacion", _resumen(resultado))
            d = pl.evaluar_paso(plan, i, resultado, intentos[i], replanes, iteraciones, consulta, area)
            plan, replanes = d["plan"], replanes + int(d["replan"])
            nota("decision", ("🔁 replanificación: " if d["replan"] else "Manager: ") + d["motivo"])
            if d["accion"] == "pedir_dato":
                return {"plan": plan, "observaciones": observaciones, "replanes": replanes, "falta": d["falta"],
                        "pausa_en": i}
            if d["accion"] == "finalizar":
                break
            i = d["siguiente"]
        return {"plan": plan, "observaciones": observaciones, "replanes": replanes}

    def _sintetizar(self, observaciones: list, intencion: str) -> str:
        """Respuesta final armada con las salidas de las herramientas (las citas ya vienen numeradas)."""
        hubo_ticket = any(o["herramienta"] == "registrar_derivacion" and not o["resultado"].get("error")
                          for o in observaciones)
        partes = [derivacion.MOTIVOS["caso_excepcional"]] if intencion == "excepcional" else []
        for o in observaciones:
            res = o["resultado"]
            if res.get("error") or res.get("falta"):
                continue
            if res.get("sin_evidencia") and hubo_ticket:
                partes.append(derivacion.MOTIVOS.get(res.get("motivo"), derivacion.MOTIVOS["sin_informacion"]))
            elif res.get("mensaje"):
                partes.append(res["mensaje"])
        if not partes and (not observaciones or any(o["resultado"].get("falta") for o in observaciones)):
            return ""
        return "\n\n".join(partes) or ("No pude completar tu solicitud con la información disponible. Te sugiero "
                                       f"consultar a {CONTACTOS['otro']}.")

    # ===================================================== estrategia reactiva
    def _reactiva(self, consulta: str, ctx: Contexto, herramientas: dict, ventana: list, nota) -> Optional[dict]:
        """ReAct con function calling nativo: AgentExecutor + create_tool_calling_agent de LangChain."""
        import warnings

        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

        from .prompts import REACTIVO_SYSTEM
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
        tools = [herramientas[n] for n in REACTIVAS]
        prompt = ChatPromptTemplate.from_messages([("system", REACTIVO_SYSTEM), MessagesPlaceholder("chat_history"),
                                                   ("human", "{input}"), MessagesPlaceholder("agent_scratchpad")])
        ejecutor = AgentExecutor(agent=create_tool_calling_agent(self.chat, tools, prompt), tools=tools,
                                 max_iterations=MAX_ITERACIONES_REACT, return_intermediate_steps=True)
        try:
            salida = ejecutor.invoke({"input": consulta, "chat_history": ventana,
                                      "perfil": json.dumps(ctx.perfil, ensure_ascii=False) if ctx.perfil else "sin datos"})
        except Exception as e:  # sin red, cuota agotada: el Manager cambia de estrategia
            nota("decision", f"Manager: el agente ReAct falló ({type(e).__name__}); se usa el plan por reglas")
            ctx.fuentes.clear()
            return None
        observaciones = []
        for i, (accion, obs) in enumerate(salida.get("intermediate_steps", [])):
            pensamiento = next((m.content for m in getattr(accion, "message_log", []) if getattr(m, "content", "")), "")
            nota("pensamiento", f"ReAct · {pensamiento or 'necesito ' + accion.tool}")
            nota("accion", f"{accion.tool}({accion.tool_input})")
            nota("observacion", _resumen(obs))
            observaciones.append({"paso": i, "herramienta": accion.tool, "agente": "consulta" if accion.tool in
                                  AGENTES_EJECUTORES["consulta"]["herramientas"] else "razonamiento",
                                  "args": accion.tool_input, "resultado": obs if isinstance(obs, dict) else {"mensaje": str(obs)}})
        texto = salida.get("output", "")
        plan = [{**pl.paso(o["herramienta"], "elegido por el agente ReAct"), "args": o["args"], "estado": "ok"}
                for o in observaciones]
        if not observaciones or "max iterations" in texto.lower():
            nota("decision", "Manager: el agente ReAct no usó herramientas o no terminó; se usa el plan por reglas")
            ctx.fuentes.clear()
            return None
        # El Manager valida: una respuesta sin evidencia documental no se entrega como cierta
        sin_evidencia = [o for o in observaciones if o["resultado"].get("sin_evidencia")]
        if sin_evidencia and not any(o["herramienta"] == "buscar_normativa" and o["resultado"].get("fuentes")
                                     for o in observaciones):
            area = sin_evidencia[0]["resultado"].get("area")
            area = area if area in CONTACTOS and area != "otro" else "academico"
            nota("decision", "🔁 Manager: la respuesta no tiene evidencia documental; se deriva con un ticket")
            res = herramientas["registrar_derivacion"].invoke({"area": area, "resumen": consulta})
            observaciones.append({"paso": len(observaciones), "herramienta": "registrar_derivacion",
                                  "agente": "escritura", "args": {"area": area}, "resultado": res})
            plan.append({**pl.paso("registrar_derivacion", "derivar sin evidencia"), "estado": "ok", "agregado": True})
            nota("observacion", _resumen(res))
            texto = derivacion.MOTIVOS["sin_informacion"] + "\n\n" + res.get("mensaje", "")
            return {"plan": plan, "observaciones": observaciones, "replanes": 1, "texto": texto}
        nota("decision", "Manager: respuesta respaldada por las herramientas")
        return {"plan": plan, "observaciones": observaciones, "replanes": 0, "texto": texto}

    # ==================================================================== apoyo
    def _recordatorio(self, tramites: list, nueva_sesion: bool, intencion: str, excluir=()) -> str:
        """Al iniciar una sesión, la memoria de largo plazo recuerda los trámites en curso."""
        tramites = [t for t in tramites if t["tramite"] not in excluir]
        if not nueva_sesion or intencion in ("seguimiento", "olvidar") or not tramites:
            return ""
        return "\n\n📌 Recuerda que tienes en curso: " + "; ".join(
            f"{NOMBRE_TRAMITE.get(t['tramite'], t['tramite']).lower()} (etapa {etapa_legible(t['etapa'])})"
            for t in tramites) + "."

    def _registrar(self, consulta: str, r: RespuestaAgente) -> None:
        if not self.registrar:
            return
        logger_uso.registrar({
            "tipo": "agente", "consulta": consulta, "intencion": r.intencion, "estrategia": r.estrategia,
            "metodo_plan": r.metodo_plan, "plan": [f"{p['herramienta']}:{p['estado']}" for p in r.plan],
            "decisiones": [t["texto"] for t in r.traza if t["tipo"] == "decision"], "replanes": r.replanes,
            "esperando": r.esperando, "derivado": r.derivado, "n_fuentes": len(r.fuentes),
            "llamadas_llm": r.llamadas_llm, "latencia_ms": r.latencia_ms}, ruta=AGENTE_LOG_PATH)


def crear_agente(memoria_db=None, salidas=None, registrar: bool = True, dir_vectorial="config") -> AgenteDuoc:
    """Ensambla el agente: pipeline RAG del EP1 + memoria + LLM de GitHub Models (si hay token).
    memoria_db=":memory:" y dir_vectorial=None crean una memoria temporal (evaluación)."""
    from .config import LLM_MODEL, LLM_MODEL_MANAGER, MEMORIA_DB, MEMORIA_VECTORIAL_DIR
    from .llm import crear_chat_llm, crear_embeddings, crear_generador
    from .pipeline import AsistenteDuoc
    from .retrieval import abrir_vectorstore, crear_recuperador

    embeddings = crear_embeddings()
    rag = AsistenteDuoc(generar=crear_generador(), recuperar=crear_recuperador(abrir_vectorstore(embeddings)),
                        registrar=False)
    chat = crear_chat_llm(LLM_MODEL)
    manager = crear_chat_llm(LLM_MODEL_MANAGER) if chat is not None and LLM_MODEL_MANAGER != LLM_MODEL else chat
    memoria = MemoriaAgente(memoria_db or MEMORIA_DB, embeddings=embeddings,
                            dir_vectorial=MEMORIA_VECTORIAL_DIR if dir_vectorial == "config" else dir_vectorial)
    return AgenteDuoc(rag=rag.consultar, memoria=memoria,
                      chat_llm=chat, chat_manager=manager, salidas=salidas or SALIDAS_DIR, registrar=registrar)
