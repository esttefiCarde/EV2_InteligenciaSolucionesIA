# Evidencia de pruebas

## EP2 (agente)

- `pytest_salida_ep2.txt`: salida de `pytest -v` (90 pruebas: herramientas, memoria, planificador, agente con LLM
  simulado y las del EP1).
- `transcripcion_agente_simulado.md`: 15 escenarios multi-turno con RAG simulado (`python scripts/evaluar_agente.py --simulado`).
- `transcripcion_agente_real_local.md`: los mismos escenarios con el índice ChromaDB real y sin token.
- `captura_interfaz_respuesta.jpg` y `captura_interfaz_traza.jpg`: la interfaz Streamlit completando el escenario E01
  (pausa por carrera y avance de malla, reanudación, memoria en la barra lateral, plan y traza).
- **Pendiente con token:** `python scripts/evaluar_agente.py` genera `transcripcion_agente_real_llm.md` y
  `evaluacion/resultados_agente_real_llm.json`. Agregar aquí capturas de la demo con GPT-4o-mini.

## EP1 (RAG)

- `pruebas_unitarias_salida.txt`: salida de las 26 pruebas del EP1.
- `python scripts/evaluar.py` genera `evaluacion/resultados_completo.json` (22 preguntas).
