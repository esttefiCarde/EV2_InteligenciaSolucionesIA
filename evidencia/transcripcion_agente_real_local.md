# Transcripción de escenarios del agente (real_local)

Generado con `python scripts/evaluar_agente.py` el 2026-11-07. Escenarios correctos: 15/15 · turnos correctos: 21/21.

## E01 · Práctica en varios turnos: falta la carrera y el avance
*Condición:* faltan datos (pausa y reanuda) · *fecha del calendario:* 2026-11-10

**Estudiante (sesión a):** Quiero empezar mi práctica, ¿cumplo los requisitos?

*Estrategia:* planificada · *plan:* reglas (sin LLM) · *herramientas:* verificar_requisitos_practica · *replanificaciones:* 0 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **pensamiento**: Manager · estrategia planificada: trámite de varios pasos: conviene ver el plan completo antes de actuar (Plan-and-Execute)
- **pensamiento**: objetivo: Iniciar la práctica profesional · plan (reglas (sin LLM)): verificar_requisitos_practica → buscar_normativa → consultar_calendario → guardar_tramite
- **pensamiento**: paso 1 · Agente de Razonamiento: comprobar el avance de malla mínimo de la carrera
- **accion**: verificar_requisitos_practica()
- **observacion**: falta el dato 'carrera'
- **decision**: Manager: verificar_requisitos_practica necesita 'carrera': se pausa el plan y se pregunta al estudiante
- **memoria**: corto plazo: el plan queda pausado hasta recibir el dato

</details>

**Asistente:**

> Para seguir necesito saber **de qué carrera eres**, porque los requisitos cambian según la carrera. ¿Cuál es tu carrera?

**Estudiante (sesión a):** Contabilidad General

*Estrategia:* planificada · *plan:* reanudado · *herramientas:* verificar_requisitos_practica · *replanificaciones:* 0 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **memoria**: largo plazo: perfil actualizado (carrera=Contabilidad General)
- **memoria**: corto plazo: el estudiante entregó 'carrera'; se reanuda el plan pausado en el paso 1
- **memoria**: corto plazo: ventana de 2 mensaje(s) (ConversationBufferWindowMemory, k=4 turnos)
- **pensamiento**: Manager · estrategia planificada: se reanuda el plan que quedó pausado
- **pensamiento**: paso 1 · Agente de Razonamiento: comprobar el avance de malla mínimo de la carrera
- **accion**: verificar_requisitos_practica()
- **observacion**: falta el dato 'avance_malla'
- **decision**: Manager: verificar_requisitos_practica necesita 'avance_malla': se pausa el plan y se pregunta al estudiante
- **memoria**: corto plazo: el plan queda pausado hasta recibir el dato

</details>

**Asistente:**

> ¿Qué **porcentaje de tu malla** llevas aprobado? Lo uso solo para este cálculo y no lo guardo.

**Estudiante (sesión a):** llevo 72

*Estrategia:* planificada · *plan:* reanudado · *herramientas:* verificar_requisitos_practica → buscar_normativa → consultar_calendario → guardar_tramite · *replanificaciones:* 0 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **memoria**: corto plazo: el estudiante entregó 'avance_malla'; se reanuda el plan pausado en el paso 1
- **memoria**: corto plazo: ventana de 4 mensaje(s) (ConversationBufferWindowMemory, k=4 turnos)
- **pensamiento**: Manager · estrategia planificada: se reanuda el plan que quedó pausado
- **pensamiento**: paso 1 · Agente de Razonamiento: comprobar el avance de malla mínimo de la carrera
- **accion**: verificar_requisitos_practica(avance_malla=72.0)
- **observacion**: cumple=True · gestion_individual=True · ✅ Cumples el avance de malla: llevas 72 % y Contabilidad General exige 70 %. La práctica dura 320 horas. [1]
- **decision**: Manager: verificar_requisitos_practica completado
- **pensamiento**: paso 2 · Agente de Consulta: obtener documentos y pasos con su fuente
- **accion**: buscar_normativa(pregunta='¿Qué documentos y pasos necesito para inscribir la práctica profesional?', area='practica_titulacion')
- **observacion**: De acuerdo con la documentación institucional de Duoc UC [2]: 1. Requisitos generales para iniciar la práctica Para inscribir la práctica profesional el estudia…
- **decision**: Manager: buscar_normativa completado
- **pensamiento**: paso 3 · Agente de Consulta: verificar que la inscripción esté abierta
- **accion**: consultar_calendario(evento='inscripcion_practica')
- **observacion**: estado=abierto · 🟢 Inscripción de práctica profesional: abierta (quedan 17 día(s) para el cierre). Período: 02-11-2026 al 27-11-2026, en la Coordinación de Práctica de tu carrer…
- **decision**: Manager: consultar_calendario completado
- **pensamiento**: paso 4 · Agente de Escritura: recordar la etapa para otra sesión
- **accion**: guardar_tramite(tramite='practica', etapa='reunir_documentos')
- **observacion**: etapa=reunir_documentos · 🗂️ Guardé tu avance en práctica profesional: etapa *reunir documentos*. Próximo paso: Reunir los documentos y pedir la carta de presentación a tu coordinación. …
- **decision**: Manager: guardar_tramite completado

</details>

**Asistente:**

> ✅ Cumples el avance de malla: llevas 72 % y Contabilidad General exige 70 %. La práctica dura 320 horas. [1]
> 
> De acuerdo con la documentación institucional de Duoc UC [2]:
> 
> 1. Requisitos generales para iniciar la práctica Para inscribir la práctica profesional el estudiante debe: (a) ser alumno regular, (b) haber aprobado el porcentaje de la malla que exige su carrera, (c) contar con una empresa o institución que lo reciba y (d) tener un seguro vigente para el período de práctica.
> 
> 📌 Te recomendamos verificar las condiciones particulares con tu Coordinación de Carrera.
> 
> 🟢 Inscripción de práctica profesional: **abierta** (quedan 17 día(s) para el cierre). Período: 02-11-2026 al 27-11-2026, en la Coordinación de Práctica de tu carrera. Fecha considerada: 10-11-2026. [3]
> 
> 🗂️ Guardé tu avance en **práctica profesional**: etapa *reunir documentos*. Próximo paso: Reunir los documentos y pedir la carta de presentación a tu coordinación. Puedes retomarlo en otra sesión.

Fuentes: [1] Manual de Práctica Profesional (simulado) – 2. Requisitos específicos por carrera; [2] Manual de Práctica Profesional (simulado) – 1. Requisitos generales para iniciar la práctica (interno, v2026.1); [3] Calendario Académico 2026-2 (simulado)


## E02 · No cumple el avance de malla
*Condición:* requisito no cumplido · *fecha del calendario:* 2026-11-10

**Estudiante (sesión a):** Quiero empezar mi práctica, soy de Ingeniería en Informática y llevo 72% de la malla

*Estrategia:* planificada · *plan:* reglas (sin LLM) · *herramientas:* verificar_requisitos_practica → buscar_normativa → guardar_tramite · *replanificaciones:* 1 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **memoria**: largo plazo: perfil actualizado (carrera=Ingeniería en Informática)
- **pensamiento**: Manager · estrategia planificada: trámite de varios pasos: conviene ver el plan completo antes de actuar (Plan-and-Execute)
- **pensamiento**: objetivo: Iniciar la práctica profesional · plan (reglas (sin LLM)): verificar_requisitos_practica → buscar_normativa → consultar_calendario → guardar_tramite
- **pensamiento**: paso 1 · Agente de Razonamiento: comprobar el avance de malla mínimo de la carrera
- **accion**: verificar_requisitos_practica(avance_malla=72.0)
- **observacion**: cumple=False · gestion_individual=True · ❌ Todavía no cumples el avance de malla: llevas 72 % y Ingeniería en Informática exige 80 % (incluye haber aprobado Ingeniería de Software); te faltan 8 puntos …
- **decision**: 🔁 replanificación: no cumple el avance de malla: se omite consultar_calendario; la etapa pasa a 'cumplir requisitos'
- **pensamiento**: paso 2 · Agente de Consulta: obtener documentos y pasos con su fuente
- **accion**: buscar_normativa(pregunta='¿Qué documentos y pasos necesito para inscribir la práctica profesional?', area='practica_titulacion')
- **observacion**: De acuerdo con la documentación institucional de Duoc UC [2]: 1. Requisitos generales para iniciar la práctica Para inscribir la práctica profesional el estudia…
- **decision**: Manager: buscar_normativa completado
- **pensamiento**: paso 4 · Agente de Escritura: recordar la etapa para otra sesión
- **accion**: guardar_tramite(tramite='practica', etapa='cumplir_requisitos', proximo_paso='Aprobar asignaturas hasta llegar al 80 % de la malla')
- **observacion**: etapa=cumplir_requisitos · 🗂️ Guardé tu avance en práctica profesional: etapa *cumplir requisitos*. Próximo paso: Aprobar asignaturas hasta llegar al 80 % de la malla. Puedes retomarlo en…
- **decision**: Manager: guardar_tramite completado

</details>

**Asistente:**

> ❌ Todavía no cumples el avance de malla: llevas 72 % y Ingeniería en Informática exige 80 % (incluye haber aprobado Ingeniería de Software); te faltan 8 puntos porcentuales. [1]
> 
> De acuerdo con la documentación institucional de Duoc UC [2]:
> 
> 1. Requisitos generales para iniciar la práctica Para inscribir la práctica profesional el estudiante debe: (a) ser alumno regular, (b) haber aprobado el porcentaje de la malla que exige su carrera, (c) contar con una empresa o institución que lo reciba y (d) tener un seguro vigente para el período de práctica.
> 
> 📌 Te recomendamos verificar las condiciones particulares con tu Coordinación de Carrera.
> 
> 🗂️ Guardé tu avance en **práctica profesional**: etapa *cumplir requisitos*. Próximo paso: Aprobar asignaturas hasta llegar al 80 % de la malla. Puedes retomarlo en otra sesión.

Fuentes: [1] Manual de Práctica Profesional (simulado) – 2. Requisitos específicos por carrera; [2] Manual de Práctica Profesional (simulado) – 1. Requisitos generales para iniciar la práctica (interno, v2026.1)


## E03 · Inscripción de práctica cerrada
*Condición:* período cerrado (fecha) · *fecha del calendario:* 2026-12-05

**Estudiante (sesión a):** Soy de Analista Programador y llevo 80% de la malla. Quiero inscribir mi práctica, prepárame la solicitud

*Estrategia:* planificada · *plan:* reglas (sin LLM) · *herramientas:* verificar_requisitos_practica → buscar_normativa → consultar_calendario → guardar_tramite · *replanificaciones:* 1 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **memoria**: largo plazo: perfil actualizado (carrera=Analista Programador)
- **pensamiento**: Manager · estrategia planificada: trámite de varios pasos: conviene ver el plan completo antes de actuar (Plan-and-Execute)
- **pensamiento**: objetivo: Iniciar la práctica profesional · plan (reglas (sin LLM)): verificar_requisitos_practica → buscar_normativa → consultar_calendario → redactar_solicitud → guardar_tramite
- **pensamiento**: paso 1 · Agente de Razonamiento: comprobar el avance de malla mínimo de la carrera
- **accion**: verificar_requisitos_practica(avance_malla=80.0)
- **observacion**: cumple=True · gestion_individual=True · ✅ Cumples el avance de malla: llevas 80 % y Analista Programador exige 75 %. La práctica dura 320 horas. [1]
- **decision**: Manager: verificar_requisitos_practica completado
- **pensamiento**: paso 2 · Agente de Consulta: obtener documentos y pasos con su fuente
- **accion**: buscar_normativa(pregunta='¿Qué documentos y pasos necesito para inscribir la práctica profesional?', area='practica_titulacion')
- **observacion**: De acuerdo con la documentación institucional de Duoc UC [2]: 1. Requisitos generales para iniciar la práctica Para inscribir la práctica profesional el estudia…
- **decision**: Manager: buscar_normativa completado
- **pensamiento**: paso 3 · Agente de Consulta: verificar que la inscripción esté abierta
- **accion**: consultar_calendario(evento='inscripcion_practica')
- **observacion**: estado=cerrado · 🔴 Inscripción de práctica profesional: cerrada (ya cerró este semestre). Período: 02-11-2026 al 27-11-2026, en la Coordinación de Práctica de tu carrera. Fecha …
- **decision**: 🔁 replanificación: el período 'inscripcion_practica' está cerrado: no se redacta la solicitud y la etapa pasa a 'esperar apertura'
- **pensamiento**: paso 5 · Agente de Escritura: recordar la etapa para otra sesión
- **accion**: guardar_tramite(tramite='practica', etapa='esperar_apertura', proximo_paso='El período ya cerró: revisa las fechas del próximo semestre con tu sede')
- **observacion**: etapa=esperar_apertura · 🗂️ Guardé tu avance en práctica profesional: etapa *esperar apertura*. Próximo paso: El período ya cerró: revisa las fechas del próximo semestre con tu sede. Pu…
- **decision**: Manager: guardar_tramite completado

</details>

**Asistente:**

> ✅ Cumples el avance de malla: llevas 80 % y Analista Programador exige 75 %. La práctica dura 320 horas. [1]
> 
> De acuerdo con la documentación institucional de Duoc UC [2]:
> 
> 1. Requisitos generales para iniciar la práctica Para inscribir la práctica profesional el estudiante debe: (a) ser alumno regular, (b) haber aprobado el porcentaje de la malla que exige su carrera, (c) contar con una empresa o institución que lo reciba y (d) tener un seguro vigente para el período de práctica.
> 
> 📌 Te recomendamos verificar las condiciones particulares con tu Coordinación de Carrera.
> 
> 🔴 Inscripción de práctica profesional: **cerrada** (ya cerró este semestre). Período: 02-11-2026 al 27-11-2026, en la Coordinación de Práctica de tu carrera. Fecha considerada: 05-12-2026. [3]
> 
> 🗂️ Guardé tu avance en **práctica profesional**: etapa *esperar apertura*. Próximo paso: El período ya cerró: revisa las fechas del próximo semestre con tu sede. Puedes retomarlo en otra sesión.

Fuentes: [1] Manual de Práctica Profesional (simulado) – 2. Requisitos específicos por carrera; [2] Manual de Práctica Profesional (simulado) – 1. Requisitos generales para iniciar la práctica (interno, v2026.1); [3] Calendario Académico 2026-2 (simulado)


## E04 · Inscripción abierta con borrador
*Condición:* período abierto · *fecha del calendario:* 2026-11-10

**Estudiante (sesión a):** Soy de Analista Programador y llevo 80% de la malla. Quiero inscribir mi práctica, prepárame la solicitud

*Estrategia:* planificada · *plan:* reglas (sin LLM) · *herramientas:* verificar_requisitos_practica → buscar_normativa → consultar_calendario → redactar_solicitud → guardar_tramite · *replanificaciones:* 0 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **memoria**: largo plazo: perfil actualizado (carrera=Analista Programador)
- **pensamiento**: Manager · estrategia planificada: trámite de varios pasos: conviene ver el plan completo antes de actuar (Plan-and-Execute)
- **pensamiento**: objetivo: Iniciar la práctica profesional · plan (reglas (sin LLM)): verificar_requisitos_practica → buscar_normativa → consultar_calendario → redactar_solicitud → guardar_tramite
- **pensamiento**: paso 1 · Agente de Razonamiento: comprobar el avance de malla mínimo de la carrera
- **accion**: verificar_requisitos_practica(avance_malla=80.0)
- **observacion**: cumple=True · gestion_individual=True · ✅ Cumples el avance de malla: llevas 80 % y Analista Programador exige 75 %. La práctica dura 320 horas. [1]
- **decision**: Manager: verificar_requisitos_practica completado
- **pensamiento**: paso 2 · Agente de Consulta: obtener documentos y pasos con su fuente
- **accion**: buscar_normativa(pregunta='¿Qué documentos y pasos necesito para inscribir la práctica profesional?', area='practica_titulacion')
- **observacion**: De acuerdo con la documentación institucional de Duoc UC [2]: 1. Requisitos generales para iniciar la práctica Para inscribir la práctica profesional el estudia…
- **decision**: Manager: buscar_normativa completado
- **pensamiento**: paso 3 · Agente de Consulta: verificar que la inscripción esté abierta
- **accion**: consultar_calendario(evento='inscripcion_practica')
- **observacion**: estado=abierto · 🟢 Inscripción de práctica profesional: abierta (quedan 17 día(s) para el cierre). Período: 02-11-2026 al 27-11-2026, en la Coordinación de Práctica de tu carrer…
- **decision**: Manager: consultar_calendario completado
- **pensamiento**: paso 4 · Agente de Escritura: preparar el borrador de inscripción
- **accion**: redactar_solicitud(tipo='inscripcion_practica')
- **observacion**: 📝 Preparé un borrador de solicitud de inscripción de práctica profesional (`inscripcion_practica_20261110.md`). Complétalo con tus datos personales antes de ent…
- **decision**: Manager: redactar_solicitud completado
- **pensamiento**: paso 5 · Agente de Escritura: recordar la etapa para otra sesión
- **accion**: guardar_tramite(tramite='practica', etapa='entregar_solicitud')
- **observacion**: etapa=entregar_solicitud · 🗂️ Guardé tu avance en práctica profesional: etapa *entregar solicitud*. Próximo paso: Completar el borrador con tus datos y entregarlo a la coordinación. Puede…
- **decision**: Manager: guardar_tramite completado

</details>

**Asistente:**

> ✅ Cumples el avance de malla: llevas 80 % y Analista Programador exige 75 %. La práctica dura 320 horas. [1]
> 
> De acuerdo con la documentación institucional de Duoc UC [2]:
> 
> 1. Requisitos generales para iniciar la práctica Para inscribir la práctica profesional el estudiante debe: (a) ser alumno regular, (b) haber aprobado el porcentaje de la malla que exige su carrera, (c) contar con una empresa o institución que lo reciba y (d) tener un seguro vigente para el período de práctica.
> 
> 📌 Te recomendamos verificar las condiciones particulares con tu Coordinación de Carrera.
> 
> 🟢 Inscripción de práctica profesional: **abierta** (quedan 17 día(s) para el cierre). Período: 02-11-2026 al 27-11-2026, en la Coordinación de Práctica de tu carrera. Fecha considerada: 10-11-2026. [3]
> 
> 📝 Preparé un borrador de **solicitud de inscripción de práctica profesional** (`inscripcion_practica_20261110.md`). Complétalo con tus datos personales antes de entregarlo.
> 
> 🗂️ Guardé tu avance en **práctica profesional**: etapa *entregar solicitud*. Próximo paso: Completar el borrador con tus datos y entregarlo a la coordinación. Puedes retomarlo en otra sesión.

Fuentes: [1] Manual de Práctica Profesional (simulado) – 2. Requisitos específicos por carrera; [2] Manual de Práctica Profesional (simulado) – 1. Requisitos generales para iniciar la práctica (interno, v2026.1); [3] Calendario Académico 2026-2 (simulado)


## E05 · Carrera sin inscripción individual
*Condición:* regla distinta por carrera · *fecha del calendario:* 2026-11-10

**Estudiante (sesión a):** Quiero inscribir mi práctica, soy de Enfermería

*Estrategia:* planificada · *plan:* reglas (sin LLM) · *herramientas:* verificar_requisitos_practica → guardar_tramite · *replanificaciones:* 1 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **memoria**: largo plazo: perfil actualizado (carrera=Enfermería)
- **pensamiento**: Manager · estrategia planificada: trámite de varios pasos: conviene ver el plan completo antes de actuar (Plan-and-Execute)
- **pensamiento**: objetivo: Iniciar la práctica profesional · plan (reglas (sin LLM)): verificar_requisitos_practica → buscar_normativa → consultar_calendario → guardar_tramite
- **pensamiento**: paso 1 · Agente de Razonamiento: comprobar el avance de malla mínimo de la carrera
- **accion**: verificar_requisitos_practica()
- **observacion**: gestion_individual=False · En Enfermería la práctica se realiza en campos clínicos que asigna la carrera; no se inscribe de forma individual. [1]
- **decision**: 🔁 replanificación: la carrera asigna los campos clínicos: se omite la inscripción individual
- **pensamiento**: paso 4 · Agente de Escritura: recordar la etapa para otra sesión
- **accion**: guardar_tramite(tramite='practica', etapa='coordinar_campo_clinico', proximo_paso='Coordinar con tu carrera la asignación del campo clínico')
- **observacion**: etapa=coordinar_campo_clinico · 🗂️ Guardé tu avance en práctica profesional: etapa *coordinar campo clínico*. Próximo paso: Coordinar con tu carrera la asignación del campo clínico. Puedes ret…
- **decision**: Manager: guardar_tramite completado

</details>

**Asistente:**

> En Enfermería la práctica se realiza en campos clínicos que asigna la carrera; no se inscribe de forma individual. [1]
> 
> 🗂️ Guardé tu avance en **práctica profesional**: etapa *coordinar campo clínico*. Próximo paso: Coordinar con tu carrera la asignación del campo clínico. Puedes retomarlo en otra sesión.

Fuentes: [1] Manual de Práctica Profesional (simulado) – 2. Requisitos específicos por carrera


## E06 · Asistencia en riesgo
*Condición:* cálculo con riesgo de reprobar · *fecha del calendario:* 2026-11-10

**Estudiante (sesión a):** En el taller falté a 12 de 30 clases, ¿repruebo por asistencia?

*Estrategia:* reactiva · *plan:* reglas (sin LLM) · *herramientas:* calcular_asistencia → buscar_normativa → buscar_normativa · *replanificaciones:* 1 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **pensamiento**: Manager · estrategia reactiva: consulta puntual: basta decidir la acción paso a paso (ReAct)
- **pensamiento**: objetivo: Calcular la situación de asistencia · plan (reglas (sin LLM)): calcular_asistencia → buscar_normativa
- **pensamiento**: paso 1 · Agente de Razonamiento: calcular el % de asistencia y las faltas restantes
- **accion**: calcular_asistencia(clases_totales=30, inasistencias=12, tipo='practica')
- **observacion**: cumple=False · ⚠️ Tu asistencia es 60 %: está bajo el mínimo de 70 % que se exige en talleres y asignaturas prácticas. Con 12 inasistencias superas el máximo permitido (9). [1…
- **decision**: 🔁 replanificación: el cálculo indica riesgo de reprobar: se agrega un paso para explicar las consecuencias según el reglamento
- **pensamiento**: paso 2 · Agente de Consulta: citar la regla de asistencia mínima
- **accion**: buscar_normativa(pregunta='¿Cuál es la asistencia mínima para aprobar una asignatura?', area='academico')
- **observacion**: De acuerdo con la documentación institucional de Duoc UC [1]: Art. 5. Asistencia La asistencia mínima para aprobar una asignatura teórica es 60 % de las clases.…
- **decision**: Manager: buscar_normativa completado
- **pensamiento**: paso 3 · Agente de Consulta: explicar qué pasa si reprueba
- **accion**: buscar_normativa(pregunta='¿Qué pasa si repruebo una asignatura?', area='academico')
- **observacion**: De acuerdo con la documentación institucional de Duoc UC [2]: Art. 8. Reprobación de asignaturas Una asignatura reprobada debe cursarse nuevamente cuando vuelva…
- **decision**: Manager: buscar_normativa completado

</details>

**Asistente:**

> ⚠️ Tu asistencia es 60 %: está bajo el mínimo de 70 % que se exige en talleres y asignaturas prácticas. Con 12 inasistencias superas el máximo permitido (9). [1]
> 
> De acuerdo con la documentación institucional de Duoc UC [1]:
> 
> Art. 5. Asistencia La asistencia mínima para aprobar una asignatura teórica es 60 % de las clases. En talleres, laboratorios y asignaturas prácticas la asistencia mínima es 70 %. Quien no cumpla la asistencia mínima reprueba la asignatura aunque su nota sea superior a 4,0.
> 
> 📌 Te recomendamos verificar las condiciones particulares con tu Coordinación de Carrera.
> 
> De acuerdo con la documentación institucional de Duoc UC [2]:
> 
> Art. 8. Reprobación de asignaturas Una asignatura reprobada debe cursarse nuevamente cuando vuelva a ofrecerse. Reprobar la misma asignatura por segunda vez genera una carta de advertencia y seguimiento académico. Reprobar la misma asignatura por tercera vez constituye causal de eliminación académica, salvo que la Dirección de la carrera acoja una apelación del estudiante.
> 
> 📌 Te recomendamos verificar las condiciones particulares con tu Coordinación de Carrera.

Fuentes: [1] Reglamento Académico (simulado) – Art. 5. Asistencia (interno, v2026.1); [2] Reglamento Académico (simulado) – Art. 8. Reprobación de asignaturas (interno, v2026.1)


## E07 · Nota necesaria para aprobar
*Condición:* cálculo · *fecha del calendario:* 2026-11-10

**Estudiante (sesión a):** Tengo un 3,5 (30%) y un 4,0 (20%), ¿qué nota necesito en lo que queda para aprobar?

*Estrategia:* reactiva · *plan:* reglas (sin LLM) · *herramientas:* calcular_nota_necesaria → buscar_normativa · *replanificaciones:* 0 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **pensamiento**: Manager · estrategia reactiva: consulta puntual: basta decidir la acción paso a paso (ReAct)
- **pensamiento**: objetivo: Calcular la nota necesaria para aprobar · plan (reglas (sin LLM)): calcular_nota_necesaria → buscar_normativa
- **pensamiento**: paso 1 · Agente de Razonamiento: calcular la nota mínima en lo que resta
- **accion**: calcular_nota_necesaria(notas=[{'nota': 3.5, 'ponderacion': 30.0}, {'nota': 4.0, 'ponderacion': 20.0}])
- **observacion**: alcanzable=True · Llevas 1,85 puntos acumulados con el 50 % evaluado. Para aprobar con 4,0 necesitas un promedio de 4,3 en el 50 % restante. [1]
- **decision**: Manager: calcular_nota_necesaria completado
- **pensamiento**: paso 2 · Agente de Consulta: citar la nota de aprobación
- **accion**: buscar_normativa(pregunta='¿Con qué nota se aprueba una asignatura?', area='academico')
- **observacion**: De acuerdo con la documentación institucional de Duoc UC [1]: Art. 4. Escala de notas y aprobación Las evaluaciones se califican en escala de 1,0 a 7,0. La nota…
- **decision**: Manager: buscar_normativa completado

</details>

**Asistente:**

> Llevas 1,85 puntos acumulados con el 50 % evaluado. Para aprobar con 4,0 necesitas un promedio de 4,3 en el 50 % restante. [1]
> 
> De acuerdo con la documentación institucional de Duoc UC [1]:
> 
> Art. 4. Escala de notas y aprobación Las evaluaciones se califican en escala de 1,0 a 7,0. La nota mínima de aprobación de una asignatura es 4,0. La nota final se calcula ponderando evaluaciones parciales, trabajos y examen, según el programa de cada asignatura.
> 
> 📌 Te recomendamos verificar las condiciones particulares con tu Coordinación de Carrera.

Fuentes: [1] Reglamento Académico (simulado) – Art. 4. Escala de notas y aprobación (interno, v2026.1)


## E08 · Pregunta sin respaldo en los documentos
*Condición:* sin evidencia · *fecha del calendario:* 2026-11-10

**Estudiante (sesión a):** ¿Cuál será el valor exacto de la cuota del arancel del próximo año?

*Estrategia:* reactiva · *plan:* reglas (sin LLM) · *herramientas:* buscar_normativa → registrar_derivacion · *replanificaciones:* 1 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **pensamiento**: Manager · estrategia reactiva: consulta puntual: basta decidir la acción paso a paso (ReAct)
- **pensamiento**: objetivo: Responder una consulta con documentos · plan (reglas (sin LLM)): buscar_normativa
- **pensamiento**: paso 1 · Agente de Consulta: responder con documentos citados
- **accion**: buscar_normativa(pregunta='¿Cuál será el valor exacto de la cuota del arancel del próximo año?')
- **observacion**: sin evidencia en los documentos (baja_relevancia)
- **decision**: 🔁 replanificación: los documentos no responden: se replanifica para derivar con un ticket en vez de responder sin fuente
- **pensamiento**: paso 2 · Agente de Escritura: derivar porque los documentos no responden
- **accion**: registrar_derivacion(area='administrativo', resumen='¿Cuál será el valor exacto de la cuota del arancel del próximo año?')
- **observacion**: ticket=TCK-99EE40 · 🎫 Registré tu caso con el código TCK-99EE40 para el Punto Estudiantil de tu sede. Una persona lo revisará y puedes preguntarme por él cuando quieras.
- **decision**: Manager: registrar_derivacion completado

</details>

**Asistente:**

> No encontré documentos suficientemente relacionados con tu consulta.
> 
> 🎫 Registré tu caso con el código **TCK-99EE40** para el Punto Estudiantil de tu sede. Una persona lo revisará y puedes preguntarme por él cuando quieras.


## E09 · Retomar el trámite en otra sesión
*Condición:* memoria de largo plazo · *fecha del calendario:* 2026-11-10

**Estudiante (sesión a):** Soy de Contabilidad General, llevo 72% de la malla y quiero empezar mi práctica

*Estrategia:* planificada · *plan:* reglas (sin LLM) · *herramientas:* verificar_requisitos_practica → buscar_normativa → consultar_calendario → guardar_tramite · *replanificaciones:* 0 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **memoria**: largo plazo: perfil actualizado (carrera=Contabilidad General)
- **pensamiento**: Manager · estrategia planificada: trámite de varios pasos: conviene ver el plan completo antes de actuar (Plan-and-Execute)
- **pensamiento**: objetivo: Iniciar la práctica profesional · plan (reglas (sin LLM)): verificar_requisitos_practica → buscar_normativa → consultar_calendario → guardar_tramite
- **pensamiento**: paso 1 · Agente de Razonamiento: comprobar el avance de malla mínimo de la carrera
- **accion**: verificar_requisitos_practica(avance_malla=72.0)
- **observacion**: cumple=True · gestion_individual=True · ✅ Cumples el avance de malla: llevas 72 % y Contabilidad General exige 70 %. La práctica dura 320 horas. [1]
- **decision**: Manager: verificar_requisitos_practica completado
- **pensamiento**: paso 2 · Agente de Consulta: obtener documentos y pasos con su fuente
- **accion**: buscar_normativa(pregunta='¿Qué documentos y pasos necesito para inscribir la práctica profesional?', area='practica_titulacion')
- **observacion**: De acuerdo con la documentación institucional de Duoc UC [2]: 1. Requisitos generales para iniciar la práctica Para inscribir la práctica profesional el estudia…
- **decision**: Manager: buscar_normativa completado
- **pensamiento**: paso 3 · Agente de Consulta: verificar que la inscripción esté abierta
- **accion**: consultar_calendario(evento='inscripcion_practica')
- **observacion**: estado=abierto · 🟢 Inscripción de práctica profesional: abierta (quedan 17 día(s) para el cierre). Período: 02-11-2026 al 27-11-2026, en la Coordinación de Práctica de tu carrer…
- **decision**: Manager: consultar_calendario completado
- **pensamiento**: paso 4 · Agente de Escritura: recordar la etapa para otra sesión
- **accion**: guardar_tramite(tramite='practica', etapa='reunir_documentos')
- **observacion**: etapa=reunir_documentos · 🗂️ Guardé tu avance en práctica profesional: etapa *reunir documentos*. Próximo paso: Reunir los documentos y pedir la carta de presentación a tu coordinación. …
- **decision**: Manager: guardar_tramite completado

</details>

**Asistente:**

> ✅ Cumples el avance de malla: llevas 72 % y Contabilidad General exige 70 %. La práctica dura 320 horas. [1]
> 
> De acuerdo con la documentación institucional de Duoc UC [2]:
> 
> 1. Requisitos generales para iniciar la práctica Para inscribir la práctica profesional el estudiante debe: (a) ser alumno regular, (b) haber aprobado el porcentaje de la malla que exige su carrera, (c) contar con una empresa o institución que lo reciba y (d) tener un seguro vigente para el período de práctica.
> 
> 📌 Te recomendamos verificar las condiciones particulares con tu Coordinación de Carrera.
> 
> 🟢 Inscripción de práctica profesional: **abierta** (quedan 17 día(s) para el cierre). Período: 02-11-2026 al 27-11-2026, en la Coordinación de Práctica de tu carrera. Fecha considerada: 10-11-2026. [3]
> 
> 🗂️ Guardé tu avance en **práctica profesional**: etapa *reunir documentos*. Próximo paso: Reunir los documentos y pedir la carta de presentación a tu coordinación. Puedes retomarlo en otra sesión.

Fuentes: [1] Manual de Práctica Profesional (simulado) – 2. Requisitos específicos por carrera; [2] Manual de Práctica Profesional (simulado) – 1. Requisitos generales para iniciar la práctica (interno, v2026.1); [3] Calendario Académico 2026-2 (simulado)

**Estudiante (sesión b):** ¿En qué quedé con mi práctica?

*Estrategia:* planificada · *plan:* reglas (sin LLM) · *herramientas:* consultar_mis_tramites · *replanificaciones:* 0 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **memoria**: largo plazo: 1 consulta(s) anterior(es) parecida(s); la más cercana del 2026-11-07 (similitud 0.63)
- **pensamiento**: Manager · estrategia planificada: trámite de varios pasos: conviene ver el plan completo antes de actuar (Plan-and-Execute)
- **pensamiento**: objetivo: Retomar los trámites en curso · plan (reglas (sin LLM)): consultar_mis_tramites
- **pensamiento**: paso 1 · Agente de Consulta: leer los trámites y tickets guardados
- **accion**: consultar_mis_tramites()
- **observacion**: Esto es lo que tengo registrado de tus trámites: • Práctica profesional: etapa *reunir documentos* (actualizado el 2026-11-07). Próximo paso: Reunir los documen…
- **decision**: Manager: consultar_mis_tramites completado

</details>

**Asistente:**

> Esto es lo que tengo registrado de tus trámites:
> • **Práctica profesional**: etapa *reunir documentos* (actualizado el 2026-11-07). Próximo paso: Reunir los documentos y pedir la carta de presentación a tu coordinación.


## E10 · Pregunta de seguimiento
*Condición:* memoria de corto plazo · *fecha del calendario:* 2026-11-10

**Estudiante (sesión a):** Soy de Ingeniería en Informática. ¿Qué documentos necesito para la práctica?

*Estrategia:* reactiva · *plan:* reglas (sin LLM) · *herramientas:* buscar_normativa · *replanificaciones:* 0 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **memoria**: largo plazo: perfil actualizado (carrera=Ingeniería en Informática)
- **pensamiento**: Manager · estrategia reactiva: consulta puntual: basta decidir la acción paso a paso (ReAct)
- **pensamiento**: objetivo: Responder una consulta con documentos · plan (reglas (sin LLM)): buscar_normativa
- **pensamiento**: paso 1 · Agente de Consulta: responder con documentos citados
- **accion**: buscar_normativa(pregunta='Soy de Ingeniería en Informática. ¿Qué documentos necesito para la práctica?')
- **observacion**: De acuerdo con la documentación institucional de Duoc UC [1]: 2. Requisitos específicos por carrera Ingeniería en Informática: haber aprobado el 80 % de la mall…
- **decision**: Manager: buscar_normativa completado

</details>

**Asistente:**

> De acuerdo con la documentación institucional de Duoc UC [1]:
> 
> 2. Requisitos específicos por carrera Ingeniería en Informática: haber aprobado el 80 % de la malla, incluyendo Ingeniería de Software; la práctica dura 360 horas. Analista Programador: haber aprobado el 75 % de la malla; la práctica dura 320 horas. Ingeniería en Administración: haber aprobado el 80 % de la malla; la práctica dura 400 horas. Contabilidad General: haber aprobado el 70 % de la malla; la práctica dura 320 horas. Enfermería: la práctica se realiza en campos clínicos asignados por la carrera y no se gestiona de forma individual.
> 
> 📌 Te recomendamos verificar las condiciones particulares con tu Coordinación de Carrera.

Fuentes: [1] Manual de Práctica Profesional (simulado) – 2. Requisitos específicos por carrera (interno, v2026.1)

**Estudiante (sesión a):** ¿y cuántas horas dura?

*Estrategia:* reactiva · *plan:* reglas (sin LLM) · *herramientas:* buscar_normativa · *replanificaciones:* 0 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **memoria**: corto plazo: pregunta de seguimiento completada con el tema anterior → «¿y cuántas horas dura? (en relación con: Soy de Ingeniería en Informática. ¿Qué documentos necesito para la práctica?)»
- **memoria**: corto plazo: ventana de 2 mensaje(s) (ConversationBufferWindowMemory, k=4 turnos)
- **memoria**: largo plazo: 1 consulta(s) anterior(es) parecida(s); la más cercana del 2026-11-07 (similitud 0.7)
- **pensamiento**: Manager · estrategia reactiva: consulta puntual: basta decidir la acción paso a paso (ReAct)
- **pensamiento**: objetivo: Responder una consulta con documentos · plan (reglas (sin LLM)): buscar_normativa
- **pensamiento**: paso 1 · Agente de Consulta: responder con documentos citados
- **accion**: buscar_normativa(pregunta='¿y cuántas horas dura? (en relación con: Soy de Ingeniería en Informática. ¿Qué documentos necesito para la práctica?)')
- **observacion**: De acuerdo con la documentación institucional de Duoc UC [1]: 2. Requisitos específicos por carrera Ingeniería en Informática: haber aprobado el 80 % de la mall…
- **decision**: Manager: buscar_normativa completado

</details>

**Asistente:**

> De acuerdo con la documentación institucional de Duoc UC [1]:
> 
> 2. Requisitos específicos por carrera Ingeniería en Informática: haber aprobado el 80 % de la malla, incluyendo Ingeniería de Software; la práctica dura 360 horas. Analista Programador: haber aprobado el 75 % de la malla; la práctica dura 320 horas. Ingeniería en Administración: haber aprobado el 80 % de la malla; la práctica dura 400 horas. Contabilidad General: haber aprobado el 70 % de la malla; la práctica dura 320 horas. Enfermería: la práctica se realiza en campos clínicos asignados por la carrera y no se gestiona de forma individual.
> 
> 📌 Te recomendamos verificar las condiciones particulares con tu Coordinación de Carrera.

Fuentes: [1] Manual de Práctica Profesional (simulado) – 2. Requisitos específicos por carrera (interno, v2026.1)


## E11 · Cambio de carrera
*Condición:* dato del perfil cambia · *fecha del calendario:* 2026-11-10

**Estudiante (sesión a):** Soy de Contabilidad General, llevo 72% de la malla y quiero empezar mi práctica

*Estrategia:* planificada · *plan:* reglas (sin LLM) · *herramientas:* verificar_requisitos_practica → buscar_normativa → consultar_calendario → guardar_tramite · *replanificaciones:* 0 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **memoria**: largo plazo: perfil actualizado (carrera=Contabilidad General)
- **pensamiento**: Manager · estrategia planificada: trámite de varios pasos: conviene ver el plan completo antes de actuar (Plan-and-Execute)
- **pensamiento**: objetivo: Iniciar la práctica profesional · plan (reglas (sin LLM)): verificar_requisitos_practica → buscar_normativa → consultar_calendario → guardar_tramite
- **pensamiento**: paso 1 · Agente de Razonamiento: comprobar el avance de malla mínimo de la carrera
- **accion**: verificar_requisitos_practica(avance_malla=72.0)
- **observacion**: cumple=True · gestion_individual=True · ✅ Cumples el avance de malla: llevas 72 % y Contabilidad General exige 70 %. La práctica dura 320 horas. [1]
- **decision**: Manager: verificar_requisitos_practica completado
- **pensamiento**: paso 2 · Agente de Consulta: obtener documentos y pasos con su fuente
- **accion**: buscar_normativa(pregunta='¿Qué documentos y pasos necesito para inscribir la práctica profesional?', area='practica_titulacion')
- **observacion**: De acuerdo con la documentación institucional de Duoc UC [2]: 1. Requisitos generales para iniciar la práctica Para inscribir la práctica profesional el estudia…
- **decision**: Manager: buscar_normativa completado
- **pensamiento**: paso 3 · Agente de Consulta: verificar que la inscripción esté abierta
- **accion**: consultar_calendario(evento='inscripcion_practica')
- **observacion**: estado=abierto · 🟢 Inscripción de práctica profesional: abierta (quedan 17 día(s) para el cierre). Período: 02-11-2026 al 27-11-2026, en la Coordinación de Práctica de tu carrer…
- **decision**: Manager: consultar_calendario completado
- **pensamiento**: paso 4 · Agente de Escritura: recordar la etapa para otra sesión
- **accion**: guardar_tramite(tramite='practica', etapa='reunir_documentos')
- **observacion**: etapa=reunir_documentos · 🗂️ Guardé tu avance en práctica profesional: etapa *reunir documentos*. Próximo paso: Reunir los documentos y pedir la carta de presentación a tu coordinación. …
- **decision**: Manager: guardar_tramite completado

</details>

**Asistente:**

> ✅ Cumples el avance de malla: llevas 72 % y Contabilidad General exige 70 %. La práctica dura 320 horas. [1]
> 
> De acuerdo con la documentación institucional de Duoc UC [2]:
> 
> 1. Requisitos generales para iniciar la práctica Para inscribir la práctica profesional el estudiante debe: (a) ser alumno regular, (b) haber aprobado el porcentaje de la malla que exige su carrera, (c) contar con una empresa o institución que lo reciba y (d) tener un seguro vigente para el período de práctica.
> 
> 📌 Te recomendamos verificar las condiciones particulares con tu Coordinación de Carrera.
> 
> 🟢 Inscripción de práctica profesional: **abierta** (quedan 17 día(s) para el cierre). Período: 02-11-2026 al 27-11-2026, en la Coordinación de Práctica de tu carrera. Fecha considerada: 10-11-2026. [3]
> 
> 🗂️ Guardé tu avance en **práctica profesional**: etapa *reunir documentos*. Próximo paso: Reunir los documentos y pedir la carta de presentación a tu coordinación. Puedes retomarlo en otra sesión.

Fuentes: [1] Manual de Práctica Profesional (simulado) – 2. Requisitos específicos por carrera; [2] Manual de Práctica Profesional (simulado) – 1. Requisitos generales para iniciar la práctica (interno, v2026.1); [3] Calendario Académico 2026-2 (simulado)

**Estudiante (sesión a):** Me cambié a Ingeniería en Informática, ¿cumplo para la práctica con 72% de la malla?

*Estrategia:* planificada · *plan:* reglas (sin LLM) · *herramientas:* verificar_requisitos_practica → buscar_normativa → guardar_tramite · *replanificaciones:* 1 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **decision**: condición cambiante: la carrera cambió de Contabilidad General a Ingeniería en Informática; los pasos siguientes usan la nueva
- **memoria**: largo plazo: perfil actualizado (carrera=Ingeniería en Informática)
- **memoria**: corto plazo: ventana de 2 mensaje(s) (ConversationBufferWindowMemory, k=4 turnos)
- **pensamiento**: Manager · estrategia planificada: trámite de varios pasos: conviene ver el plan completo antes de actuar (Plan-and-Execute)
- **pensamiento**: objetivo: Iniciar la práctica profesional · plan (reglas (sin LLM)): verificar_requisitos_practica → buscar_normativa → consultar_calendario → guardar_tramite
- **pensamiento**: paso 1 · Agente de Razonamiento: comprobar el avance de malla mínimo de la carrera
- **accion**: verificar_requisitos_practica(avance_malla=72.0)
- **observacion**: cumple=False · gestion_individual=True · ❌ Todavía no cumples el avance de malla: llevas 72 % y Ingeniería en Informática exige 80 % (incluye haber aprobado Ingeniería de Software); te faltan 8 puntos …
- **decision**: 🔁 replanificación: no cumple el avance de malla: se omite consultar_calendario; la etapa pasa a 'cumplir requisitos'
- **pensamiento**: paso 2 · Agente de Consulta: obtener documentos y pasos con su fuente
- **accion**: buscar_normativa(pregunta='¿Qué documentos y pasos necesito para inscribir la práctica profesional?', area='practica_titulacion')
- **observacion**: De acuerdo con la documentación institucional de Duoc UC [2]: 1. Requisitos generales para iniciar la práctica Para inscribir la práctica profesional el estudia…
- **decision**: Manager: buscar_normativa completado
- **pensamiento**: paso 4 · Agente de Escritura: recordar la etapa para otra sesión
- **accion**: guardar_tramite(tramite='practica', etapa='cumplir_requisitos', proximo_paso='Aprobar asignaturas hasta llegar al 80 % de la malla')
- **observacion**: etapa=cumplir_requisitos · 🗂️ Guardé tu avance en práctica profesional: etapa *cumplir requisitos*. Próximo paso: Aprobar asignaturas hasta llegar al 80 % de la malla. Puedes retomarlo en…
- **decision**: Manager: guardar_tramite completado

</details>

**Asistente:**

> ❌ Todavía no cumples el avance de malla: llevas 72 % y Ingeniería en Informática exige 80 % (incluye haber aprobado Ingeniería de Software); te faltan 8 puntos porcentuales. [1]
> 
> De acuerdo con la documentación institucional de Duoc UC [2]:
> 
> 1. Requisitos generales para iniciar la práctica Para inscribir la práctica profesional el estudiante debe: (a) ser alumno regular, (b) haber aprobado el porcentaje de la malla que exige su carrera, (c) contar con una empresa o institución que lo reciba y (d) tener un seguro vigente para el período de práctica.
> 
> 📌 Te recomendamos verificar las condiciones particulares con tu Coordinación de Carrera.
> 
> 🗂️ Guardé tu avance en **práctica profesional**: etapa *cumplir requisitos*. Próximo paso: Aprobar asignaturas hasta llegar al 80 % de la malla. Puedes retomarlo en otra sesión.

Fuentes: [1] Manual de Práctica Profesional (simulado) – 2. Requisitos específicos por carrera; [2] Manual de Práctica Profesional (simulado) – 1. Requisitos generales para iniciar la práctica (interno, v2026.1)


## E12 · Caso excepcional
*Condición:* varios factores sensibles · *fecha del calendario:* 2026-11-10

**Estudiante (sesión a):** Repetí un ramo tres veces y además tuve un problema de salud, ¿qué hago?

*Estrategia:* directa · *plan:* reglas (sin LLM) · *herramientas:* registrar_derivacion · *replanificaciones:* 0 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **pensamiento**: Manager · estrategia directa: acción crítica: la resuelve la política del Manager, sin delegar en el LLM
- **pensamiento**: objetivo: Derivar un caso excepcional a una persona · plan (reglas (sin LLM)): registrar_derivacion
- **pensamiento**: paso 1 · Agente de Escritura: dejar el caso en manos de una persona
- **accion**: registrar_derivacion(area='academico', resumen='Repetí un ramo tres veces y además tuve un problema de salud, ¿qué hago?')
- **observacion**: ticket=TCK-D7B571 · 🎫 Registré tu caso con el código TCK-D7B571 para la Coordinación de tu carrera. Una persona lo revisará y puedes preguntarme por él cuando quieras.
- **decision**: Manager: registrar_derivacion completado

</details>

**Asistente:**

> Tu situación combina varios factores y requiere revisión personalizada.
> 
> 🎫 Registré tu caso con el código **TCK-D7B571** para la Coordinación de tu carrera. Una persona lo revisará y puedes preguntarme por él cuando quieras.


## E13 · Privacidad del RUT
*Condición:* dato personal en la consulta · *fecha del calendario:* 2026-11-10

**Estudiante (sesión a):** Mi RUT es 12.345.678-5, ¿dónde pido un certificado de alumno regular?

*Estrategia:* reactiva · *plan:* reglas (sin LLM) · *herramientas:* buscar_normativa · *replanificaciones:* 0 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **guardrail**: datos personales enmascarados antes de procesar: RUT
- **pensamiento**: Manager · estrategia reactiva: consulta puntual: basta decidir la acción paso a paso (ReAct)
- **pensamiento**: objetivo: Responder una consulta con documentos · plan (reglas (sin LLM)): buscar_normativa
- **pensamiento**: paso 1 · Agente de Consulta: responder con documentos citados
- **accion**: buscar_normativa(pregunta='Mi RUT es [RUT], ¿dónde pido un certificado de alumno regular?')
- **observacion**: De acuerdo con la documentación institucional de Duoc UC [1]: Preguntas frecuentes ¿Dónde puedo solicitar un certificado? Los certificados de alumno regular se …
- **decision**: Manager: buscar_normativa completado

</details>

**Asistente:**

> ⚠️ Por tu privacidad, no necesito tu RUT ni datos personales; ya los oculté de tu consulta y no los guardo.
> 
> De acuerdo con la documentación institucional de Duoc UC [1]:
> 
> Preguntas frecuentes ¿Dónde puedo solicitar un certificado? Los certificados de alumno regular se piden en la Intranet; los demás, en el Punto Estudiantil.
> 
> 📌 Te recomendamos verificar las condiciones particulares con tu Coordinación de Carrera.

Fuentes: [1] Guía de Trámites y Certificados (simulada) – Preguntas frecuentes (interno, v2026.1)


## E14 · Titulación que aún no abre
*Condición:* período próximo · *fecha del calendario:* 2026-11-10

**Estudiante (sesión a):** Soy de Analista Programador. Quiero iniciar mi titulación, prepárame el borrador

*Estrategia:* planificada · *plan:* reglas (sin LLM) · *herramientas:* buscar_normativa → consultar_calendario → guardar_tramite · *replanificaciones:* 1 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **memoria**: largo plazo: perfil actualizado (carrera=Analista Programador)
- **pensamiento**: Manager · estrategia planificada: trámite de varios pasos: conviene ver el plan completo antes de actuar (Plan-and-Execute)
- **pensamiento**: objetivo: Iniciar el proceso de titulación · plan (reglas (sin LLM)): buscar_normativa → consultar_calendario → redactar_solicitud → guardar_tramite
- **pensamiento**: paso 1 · Agente de Consulta: obtener requisitos y documentos de titulación
- **accion**: buscar_normativa(pregunta='¿Qué requisitos y documentos necesito para iniciar el proceso de titulación?', area='practica_titulacion')
- **observacion**: De acuerdo con la documentación institucional de Duoc UC [1]: 2. Documentos para iniciar el proceso Formulario de inscripción de titulación, certificado de apro…
- **decision**: Manager: buscar_normativa completado
- **pensamiento**: paso 2 · Agente de Consulta: verificar que la inscripción esté abierta
- **accion**: consultar_calendario(evento='inscripcion_titulacion')
- **observacion**: estado=proximo · 🟡 Inscripción de titulación: aún no abre (abre en 21 día(s)). Período: 01-12-2026 al 11-12-2026, en la Coordinación de Titulación de tu carrera. Fecha considera…
- **decision**: 🔁 replanificación: el período 'inscripcion_titulacion' está proximo: no se redacta la solicitud y la etapa pasa a 'esperar apertura'
- **pensamiento**: paso 4 · Agente de Escritura: recordar la etapa para otra sesión
- **accion**: guardar_tramite(tramite='titulacion', etapa='esperar_apertura', proximo_paso='La inscripción abre el 01-12: vuelve a revisarlo ese día')
- **observacion**: etapa=esperar_apertura · 🗂️ Guardé tu avance en titulación: etapa *esperar apertura*. Próximo paso: La inscripción abre el 01-12: vuelve a revisarlo ese día. Puedes retomarlo en otra se…
- **decision**: Manager: guardar_tramite completado

</details>

**Asistente:**

> De acuerdo con la documentación institucional de Duoc UC [1]:
> 
> 2. Documentos para iniciar el proceso Formulario de inscripción de titulación, certificado de aprobación de práctica, certificado de concentración de notas y comprobante de pago de derechos de titulación según el arancel vigente.
> 
> 📌 Te recomendamos verificar las condiciones particulares con tu Coordinación de Carrera.
> 
> 🟡 Inscripción de titulación: **aún no abre** (abre en 21 día(s)). Período: 01-12-2026 al 11-12-2026, en la Coordinación de Titulación de tu carrera. Fecha considerada: 10-11-2026. [2]
> 
> 🗂️ Guardé tu avance en **titulación**: etapa *esperar apertura*. Próximo paso: La inscripción abre el 01-12: vuelve a revisarlo ese día. Puedes retomarlo en otra sesión.

Fuentes: [1] Guía de Titulación (simulada) – 2. Documentos para iniciar el proceso (interno, v2026.1); [2] Calendario Académico 2026-2 (simulado)


## E15 · Derecho al olvido
*Condición:* borrar la memoria · *fecha del calendario:* 2026-11-10

**Estudiante (sesión a):** Quiero inscribir mi práctica, soy de Enfermería

*Estrategia:* planificada · *plan:* reglas (sin LLM) · *herramientas:* verificar_requisitos_practica → guardar_tramite · *replanificaciones:* 1 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **memoria**: largo plazo: perfil actualizado (carrera=Enfermería)
- **pensamiento**: Manager · estrategia planificada: trámite de varios pasos: conviene ver el plan completo antes de actuar (Plan-and-Execute)
- **pensamiento**: objetivo: Iniciar la práctica profesional · plan (reglas (sin LLM)): verificar_requisitos_practica → buscar_normativa → consultar_calendario → guardar_tramite
- **pensamiento**: paso 1 · Agente de Razonamiento: comprobar el avance de malla mínimo de la carrera
- **accion**: verificar_requisitos_practica()
- **observacion**: gestion_individual=False · En Enfermería la práctica se realiza en campos clínicos que asigna la carrera; no se inscribe de forma individual. [1]
- **decision**: 🔁 replanificación: la carrera asigna los campos clínicos: se omite la inscripción individual
- **pensamiento**: paso 4 · Agente de Escritura: recordar la etapa para otra sesión
- **accion**: guardar_tramite(tramite='practica', etapa='coordinar_campo_clinico', proximo_paso='Coordinar con tu carrera la asignación del campo clínico')
- **observacion**: etapa=coordinar_campo_clinico · 🗂️ Guardé tu avance en práctica profesional: etapa *coordinar campo clínico*. Próximo paso: Coordinar con tu carrera la asignación del campo clínico. Puedes ret…
- **decision**: Manager: guardar_tramite completado

</details>

**Asistente:**

> En Enfermería la práctica se realiza en campos clínicos que asigna la carrera; no se inscribe de forma individual. [1]
> 
> 🗂️ Guardé tu avance en **práctica profesional**: etapa *coordinar campo clínico*. Próximo paso: Coordinar con tu carrera la asignación del campo clínico. Puedes retomarlo en otra sesión.

Fuentes: [1] Manual de Práctica Profesional (simulado) – 2. Requisitos específicos por carrera

**Estudiante (sesión a):** Borra mis datos

*Estrategia:* directa · *plan:* reglas (sin LLM) · *herramientas:* olvidar_mis_datos · *replanificaciones:* 0 · *llamadas LLM:* 0 · *verificación:* ✅

<details><summary>Traza del agente</summary>

- **memoria**: corto plazo: ventana de 2 mensaje(s) (ConversationBufferWindowMemory, k=4 turnos)
- **pensamiento**: Manager · estrategia directa: acción crítica: la resuelve la política del Manager, sin delegar en el LLM
- **pensamiento**: objetivo: Borrar los datos del estudiante · plan (reglas (sin LLM)): olvidar_mis_datos
- **pensamiento**: paso 1 · Agente de Escritura: ejercer el derecho de supresión
- **accion**: olvidar_mis_datos()
- **observacion**: 🧹 Listo: borré tu perfil, tus trámites, tus tickets, tus conversaciones y tus borradores. Desde ahora no recuerdo nada de ti.
- **decision**: Manager: olvidar_mis_datos completado

</details>

**Asistente:**

> 🧹 Listo: borré tu perfil, tus trámites, tus tickets, tus conversaciones y tus borradores. Desde ahora no recuerdo nada de ti.
