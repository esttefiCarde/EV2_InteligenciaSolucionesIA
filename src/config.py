"""Configuración central del asistente (rutas, parámetros y catálogos)."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # permite correr pruebas sin python-dotenv
    def load_dotenv(*_a, **_k):
        return False

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

# --- Rutas ---------------------------------------------------------------
DOCS_DIR = ROOT / "documentos"
MANIFEST_PATH = DOCS_DIR / "manifest.json"
CHROMA_DIR = ROOT / "chroma_db"
INDEX_STATE_PATH = CHROMA_DIR / "indice_estado.json"
LOG_PATH = ROOT / "logs" / "consultas.jsonl"
COLLECTION = "duoc_normativa"

# --- Modelos -------------------------------------------------------------
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://models.github.ai/inference")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# --- Parámetros RAG ------------------------------------------------------
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 120))
K_INTERNO = int(os.getenv("K_INTERNO", 4))
K_EXTERNO = int(os.getenv("K_EXTERNO", 2))
UMBRAL_RELEVANCIA = float(os.getenv("UMBRAL_RELEVANCIA", 0.30))
UMBRAL_ROUTER = 0.55  # bajo este valor se confirma con el clasificador por reglas

# --- Agente (EP2) --------------------------------------------------------
# Selección de modelo (clase 2.3.1): el Manager puede usar un modelo más capaz que los ejecutores.
LLM_MODEL_MANAGER = os.getenv("LLM_MODEL_MANAGER", "") or LLM_MODEL
VENTANA_MEMORIA = int(os.getenv("VENTANA_MEMORIA", 4))    # k turnos de ConversationBufferWindowMemory
MAX_ITERACIONES = int(os.getenv("MAX_ITERACIONES", 8))    # herramientas ejecutadas por turno
MAX_REPLANES = int(os.getenv("MAX_REPLANES", 3))          # replanificaciones por turno
MAX_ITERACIONES_REACT = int(os.getenv("MAX_ITERACIONES_REACT", 4))
FECHA_SIMULADA = os.getenv("FECHA_SIMULADA", "").strip()  # AAAA-MM-DD; vacío = fecha real
MEMORIA_DIR = ROOT / "memoria"
MEMORIA_DB = MEMORIA_DIR / "agente.db"                    # corto plazo persistido + largo plazo
MEMORIA_VECTORIAL_DIR = MEMORIA_DIR / "episodica"         # memoria episódica (Chroma)
SALIDAS_DIR = ROOT / "salidas"                            # borradores y tickets generados
DATOS_DIR = ROOT / "datos"
CALENDARIO_PATH = DATOS_DIR / "calendario_academico_simulado.json"
REGLAS_PATH = DATOS_DIR / "reglas_academicas.json"
AGENTE_LOG_PATH = ROOT / "logs" / "agente.jsonl"

# --- Catálogos -----------------------------------------------------------
AREAS = {
    "academico": "Académico",
    "administrativo": "Administrativo",
    "practica_titulacion": "Práctica y titulación",
    "ti": "Soporte tecnológico",
}
# Unidad humana sugerida para cada área (valores referenciales; ajustar a la sede)
CONTACTOS = {
    "academico": "la Coordinación de tu carrera",
    "administrativo": "el Punto Estudiantil de tu sede",
    "practica_titulacion": "la Coordinación de Práctica y Titulación de tu carrera",
    "ti": "la Mesa de Ayuda de TI",
    "otro": "el Punto Estudiantil de tu sede",
}
CARRERAS = [
    "Ingeniería en Informática",
    "Analista Programador",
    "Ingeniería en Administración",
    "Contabilidad General",
    "Enfermería",
    "Otra carrera",
]
