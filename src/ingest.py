"""Ingesta: carga documentos (internos y externos), los divide en chunks con metadatos,
los vectoriza y los guarda en ChromaDB. Soporta re-indexación incremental.

Uso:
    python -m src.ingest              # indexa lo nuevo o modificado
    python -m src.ingest --reset      # borra la base y reindexa todo
    python -m src.ingest --online     # intenta descargar fuentes externas (si tienen URL)
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from .config import (CHROMA_DIR, CHUNK_OVERLAP, CHUNK_SIZE, DOCS_DIR, INDEX_STATE_PATH,
                     MANIFEST_PATH)


def cargar_manifest() -> list:
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def hash_documento(entrada: dict) -> str:
    h = hashlib.sha256()
    h.update(json.dumps(entrada, sort_keys=True).encode())
    h.update((DOCS_DIR / entrada["archivo"]).read_bytes())
    return h.hexdigest()


# ------------------------------------------------------------------ descarga
def descargar_externo(entrada: dict) -> bool:
    """Descarga la URL y actualiza el archivo local (caché). Devuelve True si tuvo éxito."""
    import requests
    destino = DOCS_DIR / entrada["archivo"]
    try:
        r = requests.get(entrada["url"], timeout=20, headers={"User-Agent": "Mozilla/5.0 (EP1-ISY0101)"})
        r.raise_for_status()
        if destino.suffix.lower() == ".pdf" or "pdf" in r.headers.get("content-type", ""):
            destino = destino.with_suffix(".pdf")
            destino.write_bytes(r.content)
            entrada["archivo"] = str(destino.relative_to(DOCS_DIR))
        else:
            from bs4 import BeautifulSoup
            texto = BeautifulSoup(r.text, "html.parser").get_text("\n", strip=True)
            destino.write_text(f"# {entrada['fuente']}\n\n{texto}", encoding="utf-8")
        print(f"  [online] {entrada['doc_id']}: descargado desde {entrada['url']}")
        return True
    except Exception as e:  # sin red, bloqueo, etc. -> se usa la copia local
        print(f"  [offline] {entrada['doc_id']}: no se pudo descargar ({type(e).__name__}); se usa copia local")
        return False


# --------------------------------------------------------------------- carga
def cargar_y_dividir(entrada: dict) -> list:
    from langchain_core.documents import Document
    from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

    ruta: Path = DOCS_DIR / entrada["archivo"]
    recursivo = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""])

    if ruta.suffix.lower() == ".pdf":
        from langchain_community.document_loaders import PyPDFLoader
        paginas = PyPDFLoader(str(ruta)).load()
        chunks = recursivo.split_documents(paginas)
        for c in chunks:
            c.metadata["seccion"] = f"p. {int(c.metadata.get('page', 0)) + 1}"
    else:
        texto = ruta.read_text(encoding="utf-8")
        secciones = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "h1"), ("##", "h2")], strip_headers=False).split_text(texto)
        chunks = recursivo.split_documents(secciones)
        for c in chunks:
            c.metadata["seccion"] = c.metadata.get("h2") or c.metadata.get("h1", "")
            if c.metadata["seccion"] and not c.page_content.lstrip().startswith("#"):
                # los sub-chunks pierden su título: se repite para mejorar la recuperación
                c.page_content = f"{c.metadata['seccion']}\n{c.page_content}"

    for i, c in enumerate(chunks):
        c.metadata = {
            "doc_id": entrada["doc_id"], "fuente": entrada["fuente"], "area": entrada["area"],
            "origen": entrada["origen"], "version": entrada["version"], "url": entrada.get("url", ""),
            "seccion": c.metadata.get("seccion", ""), "chunk": i,
        }
    return chunks


# ------------------------------------------------------------------ indexado
def indexar(reset: bool = False, online: bool = False) -> None:
    from .llm import crear_embeddings
    from .retrieval import abrir_vectorstore

    if reset and CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    estado = json.loads(INDEX_STATE_PATH.read_text()) if INDEX_STATE_PATH.exists() else {}

    manifest = cargar_manifest()
    vs = abrir_vectorstore(crear_embeddings())
    total = 0

    for entrada in manifest:
        if online and entrada.get("url") and entrada["origen"] == "externo":
            descargar_externo(entrada)
        h = hash_documento(entrada)
        if estado.get(entrada["doc_id"]) == h:
            print(f"  [sin cambios] {entrada['doc_id']}")
            continue
        vs._collection.delete(where={"doc_id": entrada["doc_id"]})  # quita versión anterior
        chunks = cargar_y_dividir(entrada)
        ids = [f"{entrada['doc_id']}-{i:03d}" for i in range(len(chunks))]
        vs.add_documents(chunks, ids=ids)
        estado[entrada["doc_id"]] = h
        total += len(chunks)
        print(f"  [indexado] {entrada['doc_id']}: {len(chunks)} chunks")

    for doc_id in set(estado) - {e["doc_id"] for e in manifest}:  # documentos retirados
        vs._collection.delete(where={"doc_id": doc_id})
        estado.pop(doc_id)
        print(f"  [eliminado] {doc_id}")

    INDEX_STATE_PATH.write_text(json.dumps(estado, indent=2))
    print(f"Listo. Chunks nuevos: {total}. Total en la base: {vs._collection.count()}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reset", action="store_true", help="borra la base vectorial y reindexa todo")
    ap.add_argument("--online", action="store_true", help="intenta descargar las fuentes externas")
    a = ap.parse_args()
    indexar(reset=a.reset, online=a.online)
