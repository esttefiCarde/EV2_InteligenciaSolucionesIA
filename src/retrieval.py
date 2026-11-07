"""Recuperación sobre ChromaDB con filtros por área y origen (interno / externo)."""
from typing import Optional

from .config import CHROMA_DIR, COLLECTION, K_EXTERNO, K_INTERNO
from .modelos import Fragmento


def abrir_vectorstore(embeddings):
    from langchain_chroma import Chroma
    return Chroma(collection_name=COLLECTION, embedding_function=embeddings,
                  persist_directory=str(CHROMA_DIR),
                  collection_metadata={"hnsw:space": "cosine"})


def _a_fragmento(doc, score: float) -> Fragmento:
    m = doc.metadata
    return Fragmento(texto=doc.page_content, doc_id=m.get("doc_id", ""), fuente=m.get("fuente", ""),
                     seccion=m.get("seccion", ""), origen=m.get("origen", "interno"),
                     version=str(m.get("version", "")), area=m.get("area", ""),
                     url=m.get("url", ""), score=float(score))


def crear_recuperador(vs, k_interno: int = K_INTERNO, k_externo: int = K_EXTERNO):
    """Retorna recuperar(pregunta, area|None) -> [Fragmento] mezclando fuentes internas y externas."""

    def _buscar(pregunta, k, filtro):
        try:
            return vs.similarity_search_with_relevance_scores(pregunta, k=k, filter=filtro)
        except Exception:
            return []

    def recuperar(pregunta: str, area: Optional[str]) -> list:
        def filtro(origen):
            if area:
                return {"$and": [{"area": {"$eq": area}}, {"origen": {"$eq": origen}}]}
            return {"origen": {"$eq": origen}}

        resultados = _buscar(pregunta, k_interno, filtro("interno")) + \
                     _buscar(pregunta, k_externo, filtro("externo"))
        vistos, salida = set(), []
        for doc, score in sorted(resultados, key=lambda r: r[1], reverse=True):
            clave = (doc.metadata.get("doc_id"), doc.page_content[:60])
            if clave not in vistos:
                vistos.add(clave)
                salida.append(_a_fragmento(doc, score))
        return salida

    return recuperar


def crear_asistente():
    """Ensambla el sistema completo (LLM + embeddings + Chroma + pipeline)."""
    from .llm import crear_embeddings, crear_generador
    from .pipeline import AsistenteDuoc
    vs = abrir_vectorstore(crear_embeddings())
    return AsistenteDuoc(generar=crear_generador(), recuperar=crear_recuperador(vs))
