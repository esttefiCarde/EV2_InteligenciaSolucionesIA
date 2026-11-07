# GUÍA DE PRESENTACIÓN Y DEFENSA ORAL: EVALUACIÓN PARCIAL N°1
## Asistente Inteligente para Estudiantes Duoc UC (Multi-Agente & RAG)
### Tiempo Total: 20 Minutos (10 Min Exposición + 10 Min Preguntas)

**Asignatura**: ISY0101 – Ingeniería de Soluciones con IA  
**Integrantes**: Estephany Cárdenas & Yannella Castilla  
**Evaluadores**: Docente e Integrantes de la Comisión  

---

## 📌 Estructura General de la Presentación

| Minuto | Sección | Responsable | Indicadores Evaluados |
| :--- | :--- | :--- | :--- |
| **00:00 - 02:00** | Introducción y Planteamiento del Problema | Estephany Cárdenas | IE1, IE8 |
| **02:00 - 05:00** | Defensa del Diagrama de Arquitectura Multi-Agente | Yannella Castilla | IE4, IE7 |
| **05:00 - 08:00** | Demostración de Coherencia RAG, Trazabilidad y Citaciones | Estephany Cárdenas | IE3, IE6 |
| **08:00 - 10:00** | Conclusiones, Evaluación Cuantitativa y Cierre | Yannella Castilla | IE8, IE9 |
| **10:00 - 20:00** | Rueda de Preguntas y Defensa Técnica | Ambas Integrantes | IE6, IE7, IE8, IE9 |

---

## 🎤 Guión Detallado por Diapositiva / Sección

### 1. Introducción y Contexto Organizacional (Min 00:00 - 02:00) — *Estephany Cárdenas*
- **Apertura Técnica**: *"Buenas tardes estimado docente. Presentamos la solución tecnológica desarrollada para Duoc UC: un Asistente Inteligente Multi-Agente con Pipeline RAG..."*
- **Problema Clave**: La fragmentación documental en sedes masivas genera demoras de horas/días en resolver dudas de inasistencias, prácticas o claves de acceso, sobrecargando las coordinaciones.
- **Objetivos Medibles**: 
  - Respuesta en tiempo real 24/7.
  - Reducción del 35% de consultas repetitivas en secretaría.
  - 100% de citación en fuentes oficiales institucionales.
  - Precisión del enrutamiento >= 90%.

---

### 2. Defensa del Diagrama de Arquitectura (Min 02:00 - 05:00) — *Yannella Castilla* (IE7 & IE8)
- **Exposición del Diagrama**:
  - *"Nuestra arquitectura se divide en 4 capas desacopladas:"*
    1. **Capa Enrutadora (Agente Coordinador)**: Clasifica las intenciones mediante reglas de negocio rápidas y prompt engineering con `Temperature=0.0`.
    2. **Capa Especialista**: 4 Agentes de Dominio (`Académico`, `Administrativo`, `Práctica/Titulación`, `Soporte TI`).
    3. **Capa RAG & ChromaDB**: Chunking semántico de 500 caracteres, embeddings multilingües y filtrado estricto por metadatos.
    4. **Capa de Resguardo y Escalación (Agente de Derivación Humana)**: Intercepta consultas médicas, tercera repetición de ramos o baja confianza RAG (`< 50%`).
- **Fundamentación Técnica (IE8)**: Justificar por qué se usó un enfoque Multi-Agente en lugar de un único prompt masivo: evita contaminación de contexto, optimiza los tokens consumidos y permite actualizar reglamentos de manera independiente.

---

### 3. Exposición de Coherencia RAG y Trazabilidad (Min 05:00 - 08:00) — *Estephany Cárdenas* (IE6 & IE9)
- **Demostración de Coherencia**:
  - *"Para verificar el cumplimiento del indicador IE6, demostramos cómo la respuesta del modelo es 100% fáctica y derivada exclusivamente del vector recuperado."*
  - **Ejemplo**: Ante la pregunta *'¿Hasta cuántos días tengo para justificar una inasistencia?'*, el sistema recupera el fragmento de `reglamento_academico_sim.md`, identifica el **Artículo 2**, y responde citando explícitamente: *"Según el Reglamento Académico, Capítulo I, Artículo 2, el plazo máximo es de 5 días hábiles..."*.
- **Cero Alucinación**: Si un estudiante pregunta algo no normado (ej. *'¿Puedo pagar el arancel en criptomonedas?'*), el sistema detecta falta de coincidencia en ChromaDB y activa el protocolo de derivación.

---

### 4. Evaluación Cuantitativa y Cierre (Min 08:00 - 10:00) — *Yannella Castilla* (IE6, IE8, IE9)
- **Resultados de la Suite de Pruebas (`scripts/evaluar.py`)**:
  - **Routing Accuracy**: Alta precisión en los casos de prueba.
  - **Citation Rate**: 100% de trazabilidad de fuentes.
  - **Escalation Accuracy**: 100% de derivación oportuna en situaciones de salud/3ª repetición.
- **Cierre**: *"Nuestra propuesta no solo resuelve la consulta del estudiante, sino que resguarda la privacidad de datos bajo la Ley N°19.628 y garantiza la derivación a atención presencial cuando el reglamento lo exige."*

---

## ❓ Preguntas Frecuentes de Evaluación y Respuestas Fundamentadas (Defensa IE6 - IE9)

### Pregunta 1: ¿Por qué eligieron ChromaDB y no una base de datos vectorial en la nube como Pinecone?
- **Respuesta Técnica (IE8)**: *"Optamos por ChromaDB local por tres razones técnicas fundamentales: 1) Cumplimiento normativo y privacidad de datos de la institución, al no enviar la base documental a servidores de terceros en la nube; 2) Latencia mínima en búsquedas vectoriales locales; 3) Facilidad de re-indexación directa mediante scripts en Python."*

### Pregunta 2: ¿Cómo garantizan que el asistente no invente información si el reglamento cambia el próximo año?
- **Respuesta Técnica (IE6, IE3)**: *"Garantizamos cero alucinación combinando dos mecanismos: primero, el prompt base del especialista instruye expresamente al modelo a no responder si el contexto no contiene la respuesta; segundo, establecimos un umbral de similitud coseno de 0.50 en ChromaDB. Si el reglamento cambia, únicamente debemos re-ejecutar `python -m src.ingest --reset` para actualizar la base vectorial sin modificar la lógica del sistema."*

### Pregunta 3: ¿Qué ocurre si un estudiante escribe con faltas de ortografía o lenguaje informal?
- **Respuesta Técnica (IE9)**: *"El modelo de embeddings seleccionado (`paraphrase-multilingual-MiniLM-L12-v2`) genera vectores semánticos multilingües que capturan la intención conceptual de la frase más allá de la ortografía exacta. Además, el Agente Coordinador (Router) utiliza técnicas de clasificación semántica para derivar correctamente la consulta al especialista adecuado."*
