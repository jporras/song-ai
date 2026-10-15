# Formularios y asistente sobre MusicSpec

Entrega S02/S03/S05 — 2026-10-08. Desarrollo parcial; no cierre de sprint.

## Fuente activa y guardado

Los proyectos vinculados a MusicSpec leen formularios como proyecciones de la revisión SQLite activa. Un guardado explícito de fase escribe una única revisión de `song_specs`; no actualiza además la tabla histórica de fases. Exige la revisión vigente, respeta decisiones bloqueadas y registra procedencia USER y transformaciones. Los proyectos sin ficha conservan compatibilidad anterior.

| Formulario | Valores compartidos |
| --- | --- |
| Idea | Descripción, tipo, idioma, destinatario, BPM, tonalidad, voz e instrumentos |
| Plan musical | BPM, tonalidad, compás, arco dinámico y plan por sección |
| Letra | Idioma, tono, tema, estructura y texto literal |
| Voz | Tipo, interpretación, pronunciación y dirección por sección |
| Instrumental | Instrumentos y detalles expresivos conservados |

Los detalles de edición quedan dentro de `_editor_phases` en la misma revisión. Al primer guardado explícito se conserva la base proyectada de las fases existentes. Los detalles sin traducción ACE-Step permanecen como intención; no se presentan como parámetros ejecutables.

La letra se vincula en `_lyrics_document`, con texto, secciones, hash y trazas de formato. Cambiarla invalida su aprobación anterior. El compilador rechaza un texto distinto al de MusicSpec. Los snapshots JSON/Markdown se regeneran desde SQLite; un fallo de exportación posterior al commit se informa sin negar el guardado.

Inicializar una fase vinculada devuelve sus datos actuales. Las sugerencias IA quedan sin persistir; restaurar defaults no sustituye automáticamente decisiones existentes. El usuario revisa y guarda cambios explícitos.

## Interfaz y contexto

`music_spec_control_help` aporta ayudas de las 32 opciones musicales restantes. Junto al perfil ACE-Step, el catálogo cubre los 49 campos con significado/efecto/ejemplo sin crear valores por defecto. La prueba de cobertura verifica cada campo y ausencia de valores inventados al consultar una ficha vacía. Playwright abrió la ayuda de velocidad en viewport 390×844 y comprobó sus tres textos, sin overflow horizontal observado en esa pantalla; no acredita todos los estados móviles, dispositivo táctil real ni aprendizaje amateur.

Los 17 campos ACE-Step tienen ayuda de significado/efecto/ejemplo en `control_help` del perfil compartido. El catálogo la proyecta como `detailed_help` y ficha/editor la muestran desde esa fuente. Las explicaciones no habilitan capacidades: disponibilidad local y calidad audible requieren sus verificaciones. Prueba de catálogo asegura cobertura de todos los campos del motor; Playwright verificó apertura por teclado de la ayuda de referencia y sus tres textos. Ayudas musicales restantes y móvil/amateur pendientes.

La delegación explícita ya está disponible para `seed`, `inference_steps`, `guidance_scale` y `shift`: PATCH con valor null, revisión vigente, eliminación del override y procedencia `explicit_user_delegation`, valor anterior y transformación `omit_override_use_profile_v1`. La disposición queda `delegated_to_profile`; guardar luego un valor manual la elimina. La confirmación general sigue pendiente. El botón indica que guarda y se deshabilita mientras hay un borrador abierto. Referencias, voz personalizada y tolerancia no ofrecen este comando. SQLite conserva la decisión de delegar; registrar el default efectivo resuelto por el runtime es otro criterio pendiente.

El catálogo agrega `decision_status`, `decision_label`, `review_action` y conteos de estados separados de `decided` (presencia de valor, conservada por compatibilidad). La UI explica que valores presentes no equivalen a confirmación. Distingue elecciones guardadas, propuestas, delegaciones pendientes, faltantes y campos no aplicables. Las ayudas desplegables nativas funcionan por teclado/toque; las notas de procedencia complementan la acción. Una elección USER prevalece visualmente sobre una disposición heredada pendiente. Esta entrega explica la delegación; no añade aún un comando de aceptarla. Playwright verificó el contador, estados y apertura por teclado de la ayuda de velocidad; no todas las ayudas ni móvil/amateur.

Guardar desde una fase refresca las otras; editar la ficha refresca los formularios sin sobrescribir cambios locales posteriores. Las bases de descarte se reconstruyen desde la respuesta guardada.

El contexto del asistente incluye la misma revisión capturada con el proyecto y sus fases. Se eliminan duplicaciones del documento, conservando procedencia, decisiones y referencias al texto de las fases. Esto no acredita obediencia de un modelo real.

Las propuestas del chat se vinculan al proyecto, revisión, fase y copia de los valores del formulario al iniciar la consulta. Si cualquiera cambia durante la consulta o antes de aplicar, la UI pide consultar de nuevo. Aplicar modifica un borrador; guardar sigue siendo una decisión aparte.

## Evidencia y límites

### Propuesta aplicada y guardada

La UI conserva la propuesta aplicada mientras el usuario revisa el borrador y la envía al guardar esa fase. Se limpia al descartar, cargar otro proyecto o guardar correctamente. El backend reconstruye la propuesta determinista desde la petición y la fase vigente y verifica proyecto/revisión/hash/cambios antes de persistir.

La nueva revisión incluye `reviewed_assistant_proposal` dentro del snapshot de fase: petición, propuesta, transformación, valores guardados y aceptación/modificación por campo. La aprobación general sigue pendiente. Las revisiones SQLite conservan esa evidencia aunque una edición posterior sustituya el snapshot activo. No se crea otra fuente de verdad. [Playwright del recorrido](PLAYWRIGHT_CHAT_MUSIC_SPEC_20261008.md) comprobó propuesta 109 → elección 111, recarga y rechazo de traza alterada sin cambio de revisión.

Esta traza demuestra la correspondencia con el parser actual; no acredita una ejecución original de Gemma/Qwen ni autentica un resultado LLM. Un guardado sin cambios no crea revisión ni traza nueva.

La UI acumula hasta 20 propuestas aplicadas antes de guardar. `_editor_phases` conserva `reviewed_assistant_proposals` en orden y el campo singular mantiene la última para compatibilidad. Una propuesta posterior sobre el mismo campo marca la anterior como sustituida; el último valor se compara con la edición USER final. Placeholders de claves distintas no se sustituyen entre sí. Toda la lista se valida antes de escribir; una traza inválida rechaza el guardado completo. 10 pruebas de fases y 9 de propuestas backend, 24 frontend y build aprobados. Playwright verificó dos propuestas 113/115 y elección final 117 con ambas trazas persistidas.

### Propuestas con origen verificable — 2026-10-08

El endpoint del asistente valida la revisión solicitada antes de inferir. Cada patch incluye versión de contrato, proyecto/revisión de origen, hash de la fase persistida, petición, transformaciones y estado propuesto/sin persistir. Su productor se identifica como parser determinista de la pregunta: no se atribuyen estos valores a inferencia Gemma/Qwen ni a deseos confirmados. El frontend envía la revisión y rechaza una propuesta calculada sobre otra revisión. Cuatro pruebas backend adicionales cubren la traza, ausencia de mutaciones y rechazo previo a modelos.

El asistente consulta datos guardados; el hash identifica esa base, no el borrador local sin guardar. La protección local impide aplicar una respuesta si ese borrador cambió durante la consulta. El guardado de propuestas deterministas ya conserva el vínculo con la edición revisada, incluyendo varias aplicaciones; propuestas LLM requieren ampliación.

- 32 pruebas backend dirigidas: fases compartidas (8), edición (4), compilador (6), conservación de inputs USER (3), propuestas (9), proyección de contexto (2).
- 22 pruebas frontend aprobadas, incluyendo propuestas desactualizadas y refrescos tardíos.
- Playwright MCP sobre copia SQLite: Idea → ficha → Plan musical y ficha → Idea; recuperación tras recarga; guardado antiguo rechazado y sugerencia IA sin persistencia. Cambios de prueba únicamente en la copia QA.
- Sin inferencia real Gemma/Qwen, generación nueva ni escucha en esta entrega. Los originales Isabella/Alma permanecen preservados.

Pendientes: comandos compartidos del chat con trazabilidad integral, cobertura/delegación y ayudas restantes, consumidores históricos sin MusicSpec, flujo completo Builder/Studio y aceptación con audio real y usuarios amateur. La política de sample requiere reconciliar las instrucciones actuales con las decisiones documentadas antes de modificar sus gates.
