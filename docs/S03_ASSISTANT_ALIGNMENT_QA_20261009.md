# S03 — Alineación del asistente y QA de herramientas

## Cambios

Gemma recibe un inventario compacto de las doce operaciones del registry, su canción/revisión y exigencia de acción explícita del usuario. El mismo contexto llega a las revisiones y handoffs de tareas. Qwen mantiene el catálogo completo en compilación de ficha. No se habilita ejecución automática ni guardado de sugerencias.

La selección de contexto valida que el set pertenezca a la canción solicitada. Un `song_id` inexistente o un set ajeno se rechazan antes de inferencia; si se consulta una canción vinculada sin `set_id`, se deriva su propio set. Una canción inicial sin set conserva su contexto y no elige un set distinto. Consultar un set permite recuperar la ficha vinculada que identifica el proyecto persistido. Las revisiones antiguas siguen rechazándose.

Se corrigieron tres instrucciones contradictorias: prompt conversacional, rol Gemma y sección marcada de ACE_STEP_CAPABILITIES realmente suministrada por registry. Todas describen sample previo opcional y ficha/request confirmados. Los roles explican `music_tools` y su falta de autoridad para ejecutar. Las primeras pruebas detectaron exceso del presupuesto de rol de 2500 caracteres: se compactaron las instrucciones y se repitió el lote sin ampliar ese límite. Los hashes de steering se regeneran al leer los documentos.

## Lote backend

51 pruebas aprobadas: selección de proyecto, política conversacional, propuestas, instrucciones de sample, steering, asistencia de intención, router, rechazo, gate y proyección del contexto. Incluye rechazo de contexto cruzado antes de consultar modelos, aislamiento, propuestas no persistidas, ambos roles recibiendo el contrato vigente y los doce handlers del registry. Los providers son dobles en estas pruebas; no acreditan inferencia real ni obediencia general de Gemma/Qwen. Compileall y diff check correctos.

## Playwright MCP

Servidor aislado en `127.0.0.1:8019`; SQLite en `data/qa_music_tools_20261009`, sin modelos ni monitor de recursos. Proyecto `song_e89a916fe702`, task fixture `qa_proposal_song_e89a916fe702`, revisión `spec_rev_e0015b30b2a3`. La propuesta es un doble de prueba marcado `qa_test_double`; su metadata no constituye inferencia Qwen real.

Se cargó la ficha en la pantalla de producción y se pulsó **Rechazar propuesta y conservar mi ficha**:

- Respuesta HTTP 200 del router.
- Ficha SQLite idéntica antes y después.
- Propuesta ausente en consulta y UI después de recargar.
- Catálogo HTTP contiene doce operaciones.

Se cerraron servidor QA y navegador. No se modifica producción ni se genera audio. El escenario navega a la pantalla mediante estado Vue para aislar el control; no acredita el recorrido completo desde Biblioteca.

## Balance

S03-03 V=0.5→1 para el contrato de registro, dispatch y rechazo, con aceptación pendiente. Las verificaciones de inferencia/obediencia y audio siguen asignadas a S00/S05/S06/S10; los endpoints especializados conservan sus contratos y suites, sin declarar que el escenario de rechazo prueba toda la aplicación. Global 69,0%→69,4%. La API de producción anterior requiere reinicio para cargar el código actualizado; el steering se lee por solicitud.
