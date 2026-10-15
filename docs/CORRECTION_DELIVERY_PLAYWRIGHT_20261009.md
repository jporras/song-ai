# Corrección y entrega mediante UI/backend — 2026-10-09

Playwright MCP contra 127.0.0.1:8024, SQLite QA qa_builder_batch_20261009 y song_d0d582e3925a. Candidato preparado con WAV sintético de dos segundos y task completada simulada. No ACE-Step, Gemma/Qwen ni escucha musical/aceptación real.

## Recorrido observado

1. Selección de Studio por botón visible. Carga inicial del candidato refrescada mediante loadAceCandidateJob del proxy Vue; el arranque no se acredita como recorrido completo desde Biblioteca.
2. Formulario visible de opinión: declaración de escucha marcada exclusivamente como simulación QA, decisión changes_requested y notas identificadas QA. POST review HTTP200; opinión ligada a artefacto, plan y revisión original.
3. Selección de cambio de estilo y registro de propuesta: POST correction HTTP200. Se propone cover con fuente qa_correction_audio; la revisión de ficha permanece spec_rev_fd8be90a5783.
4. Abrir propuesta mediante botón visible solo incorpora cover/fuente al borrador. La ficha guardada no cambia.
5. Guardar para revisar: PATCH spec HTTP200; nueva revisión spec_rev_76ed905796c7, pendiente. Se conserva procedencia explicit_user_control para task_type y source_artifact_id.
6. Confirmar esta configuración: POST confirm HTTP200; revisión spec_rev_b658b010caf9 confirmada. No se interpreta como aprobación de audio.
7. Volver a Studio: propuesta original deshabilitada tras cambio de revisión. Descarga del candidato anterior sigue disponible como su propio artefacto: HTTP200, RIFF, 192044 bytes, song-ai-qa_correction_audio.wav, download.failure=null. No presenta ese audio como resultado de la nueva configuración.

## Ajustes del harness

El primer guardado no envió PATCH porque el select required no encontró la fuente: la task sintética tenía audio pero faltaba create_song_artifact. El generador real sí registra artefactos en ace_step_candidate_service.py. Se registró el artefacto QA y se refrescó el catálogo; el formulario permitió guardar sin cambio de código del producto. No desactivar validación nativa para ocultar este fallo de preparación.

La primera descarga se completó, pero el chequeo HTTP posterior usó un href relativo en page.request.get. Corregido resolviendo URL contra page.url; descarga y comprobación HTTP posteriores completadas.

## Alcance restante

La propuesta → borrador → guardado → confirmación → bloqueo de propuesta antigua → descarga del artefacto original queda verificada por UI/backend reales con candidato simulado. No se ejecutaron nuevo plan/job ni una segunda versión; tampoco recorrido desde idea. Estos gates y la corrección con audio real siguen pendientes. S06-06/S10-07 conservan V0.5; D/V89,9%. Evidencia complementa pruebas de componentes anteriores sin repetir suites. Servidor/browser cerrados; proyectos de producción intactos; sin commit/push.
