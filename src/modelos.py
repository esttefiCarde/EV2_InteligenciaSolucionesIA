"""Estructuras de datos compartidas entre módulos."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Fragmento:
    """Chunk recuperado desde la base vectorial con su trazabilidad."""
    texto: str
    doc_id: str
    fuente: str            # nombre legible del documento
    seccion: str = ""      # artículo / sección dentro del documento
    origen: str = "interno"  # interno | externo
    version: str = ""
    area: str = ""
    url: str = ""
    score: float = 0.0     # relevancia 0-1 (similitud coseno)

    def etiqueta(self) -> str:
        return f"{self.fuente} – {self.seccion}" if self.seccion else self.fuente


@dataclass
class RespuestaAgente:
    """Resultado de un turno del agente (EP2), con su traza para la interfaz y la evaluación."""
    texto: str
    fuentes: list = field(default_factory=list)
    intencion: str = ""
    estrategia: str = ""          # reactiva | planificada | directa | bloqueada
    motivo_estrategia: str = ""
    objetivo: str = ""
    metodo_plan: str = ""         # LLM (function calling) | reglas | ReAct (AgentExecutor) | reanudado
    plan: list = field(default_factory=list)
    traza: list = field(default_factory=list)   # [{"tipo": pensamiento|accion|observacion|decision|memoria|guardrail, "texto"}]
    herramientas: list = field(default_factory=list)
    replanes: int = 0
    esperando: Optional[str] = None
    derivado: bool = False
    archivos: list = field(default_factory=list)
    perfil: dict = field(default_factory=dict)
    tramites: list = field(default_factory=list)
    recuerdos: list = field(default_factory=list)
    datos_sensibles: list = field(default_factory=list)
    llamadas_llm: int = 0
    latencia_ms: int = 0


@dataclass
class Respuesta:
    texto: str
    area: str = "otro"
    confianza_router: float = 0.0
    fuentes: list = field(default_factory=list)       # lista de etiquetas citadas
    derivado: bool = False
    motivo_derivacion: Optional[str] = None
    pide_aclaracion: bool = False
    reruteado: bool = False
    datos_sensibles: list = field(default_factory=list)
    latencia_ms: int = 0
    fragmentos: list = field(default_factory=list)
