"""Fábrica del LLM (GitHub Models, API compatible con OpenAI) y de los embeddings locales con fallback inteligente."""
import re

from .config import EMBEDDING_MODEL, GITHUB_TOKEN, LLM_BASE_URL, LLM_MODEL

try:
    from langchain_core.callbacks import BaseCallbackHandler
except ImportError:  # pragma: no cover
    BaseCallbackHandler = object


class ContadorLLM(BaseCallbackHandler):
    """Cuenta las llamadas al LLM: el agente informa cuántas usa cada turno (costo y cuota)."""

    def __init__(self):
        self.llamadas = 0

    def on_chat_model_start(self, *args, **kwargs):
        self.llamadas += 1

    def on_llm_start(self, *args, **kwargs):
        self.llamadas += 1


CONTADOR = ContadorLLM()


def hay_token() -> bool:
    return bool(GITHUB_TOKEN.strip()) and "tu_token" not in GITHUB_TOKEN and "xxxx" not in GITHUB_TOKEN


_VACIAS = {"cual", "cuales", "como", "cuando", "donde", "que", "quien", "para", "por", "del", "las", "los", "una",
           "uno", "unos", "con", "sin", "mis", "tengo", "puedo", "debo", "necesito", "hago", "pasa", "sobre", "este",
           "esta", "estos", "relacion", "quiero", "saber", "hay", "son", "ser", "mas", "muy", "duoc"}
COBERTURA_MINIMA = 0.5  # fracción de los términos de la pregunta que debe contener el fragmento
# Raíces que el estudiante escribe distinto que el reglamento ('apruebo' / 'aprobación', 'ramo' / 'asignatura')
_EQUIVALENTES = {"aprue": "aprob", "repru": "repro", "ramo": "asign", "ramos": "asign"}


def _terminos(texto: str) -> set:
    """Raíces (5 letras) de las palabras con contenido: 'aprobar' y 'aprobación' comparten 'aprob'."""
    from .guardrails import normalizar
    palabras = re.findall(r"[a-zñ]+", normalizar(texto))
    return {_EQUIVALENTES.get(p[:5], p[:5]) for p in palabras if len(p) > 3 and p not in _VACIAS}


def _generador_fallback(system: str, user: str) -> str:
    """Generador local cuando no hay GITHUB_TOKEN activo: respuesta extractiva con el fragmento que mejor cubre
    la pregunta. Sin LLM nadie verifica que el fragmento responda, así que se exige que contenga la mayoría de
    los términos de la pregunta; si ninguno lo hace, responde SIN_INFORMACION y el sistema deriva (no inventa)."""
    m = re.search(r'Pregunta del estudiante: "(.*)"', user, re.DOTALL)
    pregunta = m.group(1) if m else ""
    fragmentos = re.findall(r'\[F(\d+)\][^\n]*\n(.*?)(?=\n\n\[F\d+\]|\n</contexto>|\Z)', user, re.DOTALL)
    terminos = _terminos(pregunta)
    if not fragmentos or not terminos:
        return "SIN_INFORMACION"

    def cobertura(texto):
        return len(terminos & _terminos(texto)) / len(terminos)

    numero, contexto = max(fragmentos, key=lambda f: cobertura(f[1]))  # max conserva el primero si empatan
    if cobertura(contexto) < COBERTURA_MINIMA:
        return "SIN_INFORMACION"

    lines = [line.strip().lstrip('#').strip() for line in contexto.split('\n') if line.strip()]
    return (
        f"De acuerdo con la documentación institucional de Duoc UC [F{numero}]:\n\n"
        f"{' '.join(lines[:6])}\n\n"
        f"📌 Te recomendamos verificar las condiciones particulares con tu Coordinación de Carrera."
    )


_generador_fallback.es_local = True


def crear_chat_llm(modelo: str = LLM_MODEL, max_tokens: int = 700):
    """ChatOpenAI apuntando a GitHub Models, o None si no hay token (el agente usa sus reglas)."""
    if not hay_token():
        return None
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=modelo, base_url=LLM_BASE_URL, api_key=GITHUB_TOKEN, temperature=0.0,
                      max_tokens=max_tokens, timeout=30, max_retries=2, callbacks=[CONTADOR])


def crear_generador():
    """Devuelve una función (system, user) -> texto implementada con LCEL de LangChain o fallback local."""
    if not hay_token():
        print("[INFO] GITHUB_TOKEN no detectado en .env. Usando generador sintético local.")
        return _generador_fallback

    try:
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate

        cadena = (ChatPromptTemplate.from_messages([("system", "{system}"), ("human", "{user}")])
                  | crear_chat_llm(max_tokens=500) | StrOutputParser())

        def invocar_o_fallback(system: str, user: str) -> str:
            try:
                return cadena.invoke({"system": system, "user": user})
            except Exception as e:
                print(f"[WARN] Error invocando LLM remoto ({e}). Usando generador local.")
                return _generador_fallback(system, user)

        return invocar_o_fallback
    except Exception as e:
        print(f"[WARN] Error inicializando LangChain LLM: {e}. Usando generador local.")
        return _generador_fallback


def crear_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL,
                                 encode_kwargs={"normalize_embeddings": True})
