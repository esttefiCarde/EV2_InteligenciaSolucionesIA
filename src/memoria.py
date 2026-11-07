"""Memoria del agente (EP2, IE3 e IE4), basada en los sistemas de memoria de LangChain (clase 2.2.1).

Corto plazo (por sesión)
  - ConversationBufferWindowMemory con k turnos: es lo que se inyecta en el prompt. Recortar a una
    ventana controla los tokens y el costo (context pruning).
  - Su chat_memory es HistorialSQLite: el historial completo persiste en SQLite, así que la
    conversación sobrevive a un reinicio de la aplicación.
  - Estado de la sesión: tema activo y plan pausado. Una tarea de varios turnos continúa donde quedó.
Largo plazo (por estudiante, entre sesiones)
  - Perfil declarado (carrera, sede, jornada), trámites en curso con su etapa y tickets de derivación.
  - Memoria episódica: un resumen de cada consulta en una colección Chroma propia, recuperada por
    similitud (el concepto de VectorStoreRetrieverMemory, con filtro por estudiante).
Privacidad (Ley 19.628 / Ley 21.719): solo se guarda texto enmascarado; en la memoria episódica los
números (notas, asistencia, % de malla) se reemplazan antes de guardar, y el estudiante puede pedir
que se borre todo (olvidar).
"""
import json
import re
import sqlite3
import threading
import time
import uuid
import warnings
from pathlib import Path
from typing import Optional

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict

from .config import MEMORIA_DB, MEMORIA_VECTORIAL_DIR, VENTANA_MEMORIA
from .guardrails import enmascarar

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS mensajes (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, sesion TEXT,
                                     mensaje TEXT, ts TEXT);
CREATE INDEX IF NOT EXISTS ix_mensajes ON mensajes(usuario, sesion);
CREATE TABLE IF NOT EXISTS sesiones (usuario TEXT, sesion TEXT, estado TEXT, actualizado TEXT,
                                     PRIMARY KEY (usuario, sesion));
CREATE TABLE IF NOT EXISTS perfiles (usuario TEXT PRIMARY KEY, carrera TEXT, sede TEXT, jornada TEXT,
                                     actualizado TEXT);
CREATE TABLE IF NOT EXISTS tramites (usuario TEXT, tramite TEXT, etapa TEXT, proximo_paso TEXT,
                                     actualizado TEXT, PRIMARY KEY (usuario, tramite));
CREATE TABLE IF NOT EXISTS tickets (id TEXT PRIMARY KEY, usuario TEXT, area TEXT, resumen TEXT,
                                    estado TEXT, ts TEXT);
"""


def _ahora() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


_INICIOS_SEGUIMIENTO = ("y ", "y?", "entonces", "pero ", "tambien", "ademas", "o sea")
_REFERENCIAS = (" eso", " esto", " ese ", " esa ", " lo pido", " la pido", " lo hago", " ahi", " lo mismo")


def es_seguimiento(mensaje: str) -> bool:
    """True si el mensaje depende de la conversación anterior para entenderse ("¿y cuánto dura?")."""
    from .guardrails import normalizar
    n = " " + normalizar(mensaje).strip(" ¿?¡!.,") + " "
    if not n.strip():
        return False
    return n.strip().startswith(_INICIOS_SEGUIMIENTO) or any(r in n for r in _REFERENCIAS) or len(n.split()) <= 3


def contextualizar(mensaje: str, tema: Optional[dict]) -> str:
    """Sin LLM: completa una pregunta de seguimiento con el tema activo de la memoria de corto plazo."""
    if not tema or not tema.get("consulta") or not es_seguimiento(mensaje):
        return mensaje
    return f"{mensaje} (en relación con: {tema['consulta']})"


def anonimizar(texto: str, largo: int = 300) -> str:
    """Texto apto para memoria de largo plazo: sin RUT/correo y sin cifras personales."""
    texto = re.sub(r"\d+(?:[.,]\d+)?\s*%?", "#", enmascarar(texto))
    texto = " ".join(texto.split())
    return texto if len(texto) <= largo else texto[: largo - 1] + "…"


class BaseDatos:
    """SQLite compartido por las memorias (Streamlit atiende cada sesión en un hilo distinto)."""

    def __init__(self, ruta=MEMORIA_DB):
        ruta = str(ruta)
        if ruta != ":memory:":
            Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        self._con = sqlite3.connect(ruta, check_same_thread=False)
        self._con.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock, self._con:
            self._con.executescript(_ESQUEMA)

    def q(self, sql: str, params=(), uno: bool = False):
        with self._lock, self._con:
            filas = [dict(f) for f in self._con.execute(sql, params).fetchall()]
        return (filas[0] if filas else None) if uno else filas

    def borrar(self, sql: str, params=()) -> int:
        with self._lock, self._con:
            return self._con.execute(sql, params).rowcount


# =================================================================== corto plazo
class HistorialSQLite(BaseChatMessageHistory):
    """Historial de chat persistente (HumanMessage / AIMessage) de una sesión."""

    def __init__(self, db: BaseDatos, usuario: str, sesion: str):
        self.db, self.usuario, self.sesion = db, usuario, sesion

    @property
    def messages(self) -> list:
        filas = self.db.q("SELECT mensaje FROM mensajes WHERE usuario=? AND sesion=? ORDER BY id",
                          (self.usuario, self.sesion))
        return messages_from_dict([json.loads(f["mensaje"]) for f in filas])

    def add_messages(self, messages: list) -> None:
        for m in messages:
            self.db.q("INSERT INTO mensajes (usuario, sesion, mensaje, ts) VALUES (?,?,?,?)",
                      (self.usuario, self.sesion, json.dumps(message_to_dict(m), ensure_ascii=False), _ahora()))

    def clear(self) -> None:
        self.db.borrar("DELETE FROM mensajes WHERE usuario=? AND sesion=?", (self.usuario, self.sesion))


# =================================================================== largo plazo
class MemoriaEpisodica:
    """Episodios del estudiante en Chroma, recuperados por similitud semántica."""

    def __init__(self, embeddings, directorio: Optional[Path] = MEMORIA_VECTORIAL_DIR,
                 coleccion: str = "memoria_episodica"):
        from langchain_chroma import Chroma
        extra = {"persist_directory": str(directorio)} if directorio else {}
        self.vs = Chroma(collection_name=coleccion, embedding_function=embeddings,
                         collection_metadata={"hnsw:space": "cosine"}, **extra)

    def guardar(self, usuario: str, texto: str, area: str) -> None:
        self.vs.add_texts([texto], metadatas=[{"usuario": usuario, "area": area, "fecha": _ahora()[:10]}],
                          ids=[uuid.uuid4().hex])

    def recordar(self, usuario: str, consulta: str, k: int = 2, umbral: float = 0.55) -> list:
        try:
            resultados = self.vs.similarity_search_with_relevance_scores(consulta, k=k, filter={"usuario": usuario})
        except Exception:  # colección vacía o sin episodios de este estudiante
            return []
        return [{"texto": d.page_content, "fecha": d.metadata.get("fecha", ""), "area": d.metadata.get("area", ""),
                 "similitud": round(s, 2)} for d, s in resultados if s >= umbral]

    def olvidar(self, usuario: str) -> int:
        ids = self.vs.get(where={"usuario": usuario}).get("ids", [])
        if ids:
            self.vs.delete(ids=ids)
        return len(ids)


class MemoriaAgente:
    """Fachada de memoria que usa el agente: corto plazo por sesión y largo plazo por estudiante."""
    CAMPOS_PERFIL = ("carrera", "sede", "jornada")

    def __init__(self, ruta=MEMORIA_DB, embeddings=None, ventana: int = VENTANA_MEMORIA,
                 dir_vectorial: Optional[Path] = MEMORIA_VECTORIAL_DIR):
        self.db = BaseDatos(ruta)
        self.k = ventana
        self.episodica = MemoriaEpisodica(embeddings, dir_vectorial) if embeddings is not None else None

    # ------------------------------------------------------------ corto plazo
    def memoria_conversacion(self, usuario: str, sesion: str):
        """ConversationBufferWindowMemory de LangChain sobre el historial persistente de la sesión."""
        from langchain_classic.memory import ConversationBufferWindowMemory
        with warnings.catch_warnings():  # clase de langchain-classic, la vista en clases
            warnings.simplefilter("ignore")
            return ConversationBufferWindowMemory(
                k=self.k, chat_memory=HistorialSQLite(self.db, usuario, sesion), return_messages=True,
                memory_key="chat_history", input_key="input", output_key="output")

    def ventana(self, usuario: str, sesion: str) -> list:
        """Últimos k turnos (lo que ve el LLM)."""
        return self.memoria_conversacion(usuario, sesion).load_memory_variables({})["chat_history"]

    def guardar_turno(self, usuario: str, sesion: str, entrada: str, salida: str) -> None:
        self.memoria_conversacion(usuario, sesion).save_context({"input": enmascarar(entrada)},
                                                               {"output": salida[:1200]})

    def n_mensajes(self, usuario: str, sesion: str) -> int:
        return self.db.q("SELECT COUNT(*) AS n FROM mensajes WHERE usuario=? AND sesion=?",
                         (usuario, sesion), uno=True)["n"]

    def estado(self, usuario: str, sesion: str) -> dict:
        fila = self.db.q("SELECT estado FROM sesiones WHERE usuario=? AND sesion=?", (usuario, sesion), uno=True)
        return json.loads(fila["estado"]) if fila else {}

    def guardar_estado(self, usuario: str, sesion: str, estado: dict) -> None:
        self.db.q("INSERT OR REPLACE INTO sesiones (usuario, sesion, estado, actualizado) VALUES (?,?,?,?)",
                  (usuario, sesion, json.dumps(estado, ensure_ascii=False), _ahora()))

    # ------------------------------------------------------------ largo plazo
    def perfil(self, usuario: str) -> dict:
        fila = self.db.q("SELECT carrera, sede, jornada FROM perfiles WHERE usuario=?", (usuario,), uno=True)
        return {k: v for k, v in (fila or {}).items() if v}

    def actualizar_perfil(self, usuario: str, **campos) -> dict:
        campos = {k: v for k, v in campos.items() if k in self.CAMPOS_PERFIL and v}
        if campos:
            actual = {**self.perfil(usuario), **campos}
            self.db.q("INSERT OR REPLACE INTO perfiles (usuario, carrera, sede, jornada, actualizado) "
                      "VALUES (?,?,?,?,?)", (usuario, actual.get("carrera"), actual.get("sede"),
                                             actual.get("jornada"), _ahora()))
        return self.perfil(usuario)

    def tramites(self, usuario: str) -> list:
        return self.db.q("SELECT tramite, etapa, proximo_paso, actualizado FROM tramites WHERE usuario=? "
                         "ORDER BY actualizado DESC", (usuario,))

    def guardar_tramite(self, usuario: str, tramite: str, etapa: str, proximo_paso: str) -> dict:
        self.db.q("INSERT OR REPLACE INTO tramites (usuario, tramite, etapa, proximo_paso, actualizado) "
                  "VALUES (?,?,?,?,?)", (usuario, tramite, etapa, anonimizar(proximo_paso, 200), _ahora()))
        return {"tramite": tramite, "etapa": etapa, "proximo_paso": proximo_paso}

    def tickets(self, usuario: str) -> list:
        return self.db.q("SELECT id, area, resumen, estado, ts FROM tickets WHERE usuario=? ORDER BY ts DESC",
                         (usuario,))

    def crear_ticket(self, usuario: str, area: str, resumen: str) -> str:
        ticket = "TCK-" + uuid.uuid4().hex[:6].upper()
        self.db.q("INSERT INTO tickets (id, usuario, area, resumen, estado, ts) VALUES (?,?,?,?,?,?)",
                  (ticket, usuario, area, anonimizar(resumen), "abierto", _ahora()))
        return ticket

    def guardar_episodio(self, usuario: str, consulta: str, resultado: str, area: str) -> None:
        if self.episodica is not None:
            try:
                self.episodica.guardar(usuario, f"{anonimizar(consulta, 200)} → {anonimizar(resultado, 160)}", area)
            except Exception:  # la memoria nunca debe interrumpir la atención
                pass

    def recordar(self, usuario: str, consulta: str, k: int = 2) -> list:
        return self.episodica.recordar(usuario, consulta, k=k) if self.episodica is not None else []

    def olvidar(self, usuario: str) -> dict:
        """Derecho de supresión: borra la memoria de corto y largo plazo del estudiante."""
        borrados = {t: self.db.borrar(f"DELETE FROM {t} WHERE usuario=?", (usuario,))
                    for t in ("mensajes", "sesiones", "perfiles", "tramites", "tickets")}
        if self.episodica is not None:
            borrados["episodios"] = self.episodica.olvidar(usuario)
        return borrados
