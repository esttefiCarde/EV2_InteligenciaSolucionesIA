"""Orquestador del sistema multiagente.

Flujo: guardrails -> coordinador -> (aclaración carrera) -> recuperación RAG ->
agente especialista -> verificación -> respuesta con fuentes | derivación humana.

Las dependencias (LLM y recuperador) se inyectan como funciones para poder probar la
lógica sin red ni modelos (ver tests/).
"""
import re
import time
from typing import Callable, Optional

from . import derivacion, guardrails, logger_uso, router
from .config import AREAS, UMBRAL_RELEVANCIA
from .modelos import Fragmento, Respuesta
from .prompts import USER_ESPECIALISTA, prompt_especialista

Generador = Callable[[str, str], str]                          # (system, user) -> texto
Recuperador = Callable[[str, Optional[str]], list]            # (pregunta, area|None) -> [Fragmento]

_SALUDOS = ("hola", "buenas", "buenos dias", "buenas tardes", "gracias", "chao", "adios")
MAX_FRAGMENTOS = 5


def _es_saludo(texto: str) -> bool:
    n = guardrails.normalizar(texto).strip(" ¡!.,?¿")
    return len(n.split()) <= 4 and any(n.startswith(s) for s in _SALUDOS)


def _formatear_contexto(fragmentos: list) -> str:
    bloques = []
    for i, f in enumerate(fragmentos, 1):
        cab = f"[F{i}] Fuente: {f.etiqueta()} | origen: {f.origen} | versión: {f.version or 's/i'}"
        bloques.append(f"{cab}\n{f.texto.strip()}")
    return "\n\n".join(bloques)


def _renumerar_citas(texto: str, fragmentos: list) -> tuple:
    """Convierte [F3][F1] en [1][2] y devuelve (texto, fuentes usadas en orden)."""
    usados, mapa = [], {}
    for m in re.finditer(r"\[F(\d+)\]", texto):
        idx = int(m.group(1))
        if 1 <= idx <= len(fragmentos) and idx not in mapa:
            usados.append(idx)
            mapa[idx] = len(usados)
    if not usados:  # el LLM no citó: se informan todos los fragmentos que recibió
        usados = list(range(1, len(fragmentos) + 1))
        mapa = {i: i for i in usados}
    texto = re.sub(r"\[F(\d+)\]", lambda m: f"[{mapa[int(m.group(1))]}]" if int(m.group(1)) in mapa else "", texto)
    fuentes = []
    for idx in usados:
        f = fragmentos[idx - 1]
        fuentes.append(f"[{mapa[idx]}] {f.etiqueta()} ({f.origen}, v{f.version or 's/i'})")
    return texto.strip(), fuentes


class AsistenteDuoc:
    def __init__(self, generar: Generador, recuperar: Recuperador, umbral: float = UMBRAL_RELEVANCIA,
                 registrar: bool = True):
        self.generar = generar
        self.recuperar = recuperar
        self.umbral = umbral
        self.registrar = registrar

    # ------------------------------------------------------------------ API
    def consultar(self, pregunta: str, carrera: Optional[str] = None, area: Optional[str] = None) -> Respuesta:
        """area: sugerencia del agente (EP2). Si es válida se omite la llamada al coordinador (ahorra un LLM)."""
        t0 = time.time()
        sensibles = guardrails.detectar_datos_sensibles(pregunta)
        q = guardrails.enmascarar(pregunta)  # lo que sigue NUNCA ve el RUT/correo original

        resp = self._procesar(q, carrera, area)
        resp.datos_sensibles = sensibles
        resp.latencia_ms = int((time.time() - t0) * 1000)
        if sensibles:
            resp.texto = ("⚠️ Por tu privacidad, no necesito tu RUT ni datos personales; "
                          "ya los oculté de tu consulta.\n\n") + resp.texto
        self._log(q, carrera, resp)
        return resp

    # ------------------------------------------------------------- internos
    def _derivar(self, q: str, area: str, motivo: str, **kw) -> Respuesta:
        return Respuesta(texto=derivacion.construir_mensaje(motivo, area, q), area=area,
                         derivado=True, motivo_derivacion=motivo, **kw)

    def _procesar(self, q: str, carrera: Optional[str], area_sugerida: Optional[str] = None) -> Respuesta:
        if guardrails.detectar_inyeccion(q):
            return self._derivar(q, "otro", "inyeccion")
        if _es_saludo(q):
            return Respuesta(texto="¡Hola! Soy el asistente para estudiantes de Duoc UC. Puedo ayudarte con "
                                   "dudas académicas, trámites y certificados, práctica y titulación, o "
                                   "problemas con plataformas. ¿Qué necesitas saber?")
        if guardrails.es_caso_sensible(q):
            area, _ = router.clasificar_por_palabras(q)
            return self._derivar(q, area, "sensible")

        if area_sugerida in AREAS:
            ruta = {"area": area_sugerida, "confianza": 1.0, "carrera": None}
        else:
            ruta = router.clasificar(q, self.generar)
        area, conf = ruta["area"], ruta["confianza"]
        carrera = carrera or ruta.get("carrera")

        if guardrails.es_caso_excepcional(q):
            return self._derivar(q, area, "caso_excepcional", confianza_router=conf)

        if guardrails.requiere_carrera(q, carrera):
            return Respuesta(texto="Para darte información correcta necesito saber de qué carrera eres, "
                                   "porque este procedimiento cambia según la carrera (y a veces la sede). "
                                   "¿Cuál es tu carrera?", area=area, confianza_router=conf,
                             pide_aclaracion=True)

        # --- Recuperación (con re-ruteo si el área elegida no tiene evidencia) ---
        reruteado = False
        frags = self.recuperar(q, area) if area != "otro" else []
        if not derivacion.evaluar_confianza(frags, self.umbral):
            globales = self.recuperar(q, None)
            if derivacion.evaluar_confianza(globales, self.umbral):
                mejor = max(globales, key=lambda f: f.score)
                if mejor.area in AREAS:
                    reruteado = mejor.area != area
                    area = mejor.area
                    frags = self.recuperar(q, area)
        if not derivacion.evaluar_confianza(frags, self.umbral):
            motivo = "fuera_de_alcance" if area == "otro" else "baja_relevancia"
            return self._derivar(q, area, motivo, confianza_router=conf)

        frags = sorted(frags, key=lambda f: f.score, reverse=True)[:MAX_FRAGMENTOS]

        # --- Agente especialista ---
        user = USER_ESPECIALISTA.format(contexto=_formatear_contexto(frags),
                                        carrera=carrera or "no indicada", pregunta=q)
        try:
            salida = self.generar(prompt_especialista(area), user).strip()
        except Exception:
            return self._derivar(q, area, "error_servicio", confianza_router=conf, fragmentos=frags)

        if "SIN_INFORMACION" in salida:
            return self._derivar(q, area, "sin_informacion", confianza_router=conf,
                                 reruteado=reruteado, fragmentos=frags)

        texto, fuentes = _renumerar_citas(salida, frags)
        return Respuesta(texto=texto, area=area, confianza_router=conf, fuentes=fuentes,
                         reruteado=reruteado, fragmentos=frags)

    def _log(self, q: str, carrera: Optional[str], r: Respuesta) -> None:
        if not self.registrar:
            return
        logger_uso.registrar({
            "pregunta": q, "carrera": carrera, "area": r.area, "conf_router": r.confianza_router,
            "derivado": r.derivado, "motivo": r.motivo_derivacion, "aclaracion": r.pide_aclaracion,
            "reruteado": r.reruteado, "n_fuentes": len(r.fuentes), "fuentes": r.fuentes,
            "latencia_ms": r.latencia_ms, "datos_sensibles": r.datos_sensibles,
        })


def formatear(resp: Respuesta) -> str:
    """Texto final para consola: respuesta + fuentes."""
    if not resp.fuentes:
        return resp.texto
    return resp.texto + "\n\nFuentes:\n" + "\n".join(resp.fuentes)
