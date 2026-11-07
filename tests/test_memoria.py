"""Memoria de corto plazo (ventana persistente y estado de sesión) y de largo plazo."""
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.messages import AIMessage, HumanMessage

from src.memoria import MemoriaAgente, anonimizar, contextualizar, es_seguimiento


def test_ventana_guarda_solo_los_ultimos_k_turnos():
    m = MemoriaAgente(":memory:", ventana=2)
    for i in range(4):
        m.guardar_turno("ana", "s1", f"pregunta {i}", f"respuesta {i}")
    ventana = m.ventana("ana", "s1")
    assert [type(x) for x in ventana] == [HumanMessage, AIMessage, HumanMessage, AIMessage]
    assert ventana[0].content == "pregunta 2"            # ConversationBufferWindowMemory(k=2)
    assert m.n_mensajes("ana", "s1") == 8                 # el historial completo sigue persistido


def test_el_historial_sobrevive_a_un_reinicio(tmp_path):
    ruta = tmp_path / "agente.db"
    MemoriaAgente(ruta).guardar_turno("ana", "s1", "¿Qué necesito para la práctica?", "Carta de presentación…")
    MemoriaAgente(ruta).guardar_estado("ana", "s1", {"pendiente": {"falta": "carrera"}})
    nueva = MemoriaAgente(ruta)  # otra instancia = la app se reinició
    assert nueva.ventana("ana", "s1")[0].content == "¿Qué necesito para la práctica?"
    assert nueva.estado("ana", "s1")["pendiente"]["falta"] == "carrera"


def test_las_sesiones_y_los_usuarios_no_se_mezclan():
    m = MemoriaAgente(":memory:")
    m.guardar_turno("ana", "s1", "hola", "hola")
    assert m.ventana("ana", "s2") == [] and m.ventana("bea", "s1") == []


def test_el_rut_no_llega_al_historial():
    m = MemoriaAgente(":memory:")
    m.guardar_turno("ana", "s1", "mi RUT es 12.345.678-5", "ok")
    assert "12.345.678" not in m.ventana("ana", "s1")[0].content


def test_perfil_y_tramites_entre_sesiones():
    m = MemoriaAgente(":memory:")
    m.actualizar_perfil("ana", carrera="Contabilidad General", nota="no se guarda")
    m.guardar_tramite("ana", "practica", "reunir_documentos", "Pedir la carta")
    assert m.perfil("ana") == {"carrera": "Contabilidad General"}
    assert m.tramites("ana")[0]["etapa"] == "reunir_documentos"


def test_olvidar_borra_todo_del_estudiante():
    m = MemoriaAgente(":memory:")
    m.actualizar_perfil("ana", carrera="Enfermería")
    m.guardar_turno("ana", "s1", "hola", "hola")
    m.crear_ticket("ana", "academico", "caso")
    m.actualizar_perfil("bea", carrera="Contabilidad General")
    m.olvidar("ana")
    assert m.perfil("ana") == {} and m.tickets("ana") == [] and m.ventana("ana", "s1") == []
    assert m.perfil("bea")  # los demás no se tocan


def test_memoria_episodica_recupera_por_similitud_y_por_estudiante():
    m = MemoriaAgente(":memory:", embeddings=DeterministicFakeEmbedding(size=32), dir_vectorial=None)
    m.guardar_episodio("epi_ana", "¿Qué documentos necesito para la práctica?", "Iniciar la práctica", "practica")
    recuerdos = m.recordar("epi_ana", "¿Qué documentos necesito para la práctica? → Iniciar la práctica")
    assert recuerdos and recuerdos[0]["area"] == "practica"
    assert m.recordar("epi_bea", "¿Qué documentos necesito para la práctica? → Iniciar la práctica") == []
    m.olvidar("epi_ana")
    assert m.recordar("epi_ana", "¿Qué documentos necesito para la práctica? → Iniciar la práctica") == []


def test_anonimizar_quita_cifras_y_rut():
    assert anonimizar("llevo 72% y mi RUT es 12.345.678-5") == "llevo # y mi RUT es [RUT]"


def test_preguntas_de_seguimiento():
    assert es_seguimiento("¿y cuántas horas dura?") and not es_seguimiento("¿Qué necesito para titularme el próximo año?")
    tema = {"consulta": "¿Qué necesito para la práctica?"}
    assert contextualizar("¿y cuánto dura?", tema).endswith("(en relación con: ¿Qué necesito para la práctica?)")
