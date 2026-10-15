# Lote UI/backend: navegación y sample opcional — 2026-10-09

## Correcciones

Playwright detectó mensajes antiguos en Revisar: MIDI aparecía como paso obligatorio y el encabezado del sample decía «Revisión corta obligatoria». Además, productionProcessSteps bloqueaba MASTERING/EXPORT por sampleCheckpointStatus.ready, que actualmente es false incluso para sample aprobado. Eliminado ese bloqueo; se conserva confirmación de ficha, estado ejecutable y exclusión de trabajos. El backend sigue validando set, revisión, request, fuentes y archivos.

La guía ahora describe idea, instrumental, melodía vocal, letra, configuración/plan confirmados y archivos disponibles. No promete MIDI ni formatos todavía no generados. Herramientas históricas se conservan.

## Evidencia agrupada

- 59 pruebas frontend aprobadas; cero fallos/omitidas/canceladas.
- 20 pruebas backend aprobadas: test_sample_gate, test_assistant_sample_guidance y test_user_input_persistence_request.
- Build Vite aprobado. Primer intento restringido falló por acceso esbuild fuera del workspace; reintento autorizado completó el build.
- Playwright MCP sobre backend/SQLite QA reales, 127.0.0.1:8024, proyecto song_d0d582e3925a / qa-builder-batch-set. Datos propios bajo data/qa_builder_batch_20261009; providers simulados y modelos deshabilitados en el servidor QA.
- Siete pasos navegados mediante controles visibles; cada guardado UI-state respondió HTTP200. 21 combinaciones de pantalla/anchura (390, 768, 1440 px), sin overflow horizontal.
- Studio restaurado después de recarga; aria-current=step. Ayuda «Qué significa» abierta con Enter, foco conservado y contorno visible.
- Cuatro escenarios del computed real compilado, con contexto simulado: MASTERING/EXPORT con ficha confirmada habilitan acción; ficha pendiente la bloquea. Getter de sample lanza error si se consulta: ningún caso lo consultó. No se pulsaron acciones de generación.
- Sin errores de consola en la lectura realizada. No equivale a auditoría completa de accesibilidad o contraste condicional.

Regresión reproducible en scripts/playwright_builder_regression.js mediante browser_run_code_unsafe, con proyecto QA cargado. El primer ensayo de recarga esperaba Studio antes de terminar los PUT serializados; el harness ahora espera la respuesta del guardado específico, sin modificar la persistencia del producto. El primer intento de ayuda buscaba un button; es un summary nativo, corregido en el harness.

## Estado y siguientes gates

Este lote corrige una regresión de S01-01 y amplía evidencia de S06-01/S10-07; no completa contraste/accesibilidad integral ni el recorrido con modelos/audio reales. Estados D/V no cambian; global 89,9%. Pendientes: cerrar el lote ligero UI/backend restante, después Gemma/Qwen reales y finalmente ACE-Step según VERIFICATION_STRATEGY.md. No inferencia, nueva canción, cambios a Isabella/Alma de producción ni commit/push.
