# Nuevo plan y segundo candidato simulado — 2026-10-09

Continuación del recorrido CORRECTION_DELIVERY_PLAYWRIGHT_20261009.md sobre la misma SQLite QA, song_d0d582e3925a. Servidor 8024 con dispatcher/jobs/SQLite y revisión de plan reales. Únicamente generate/preflight de los jobs sustituidos por dobles identificados QA; orchestrator de audio desactivado para no liberar/cargar modelos. El generador copia un WAV sintético y registra otro artefacto; no ejecuta Cover ni demuestra calidad, recursos o handoffs reales.

## Resultados Playwright

- Botón Generar → Preparar un nuevo plan. Editor muestra la letra QA guardada: «## VERSO / Duerme, Alma, sueña.».
- Preparar para revisar POST200: ace_plan_5827761aaa2e4eefbfdef122b3b50dd7, revisión spec_rev_b658b010caf9, task_type cover. No se usa revisión anterior de la propuesta.
- Checkbox de revisión de plan/letra y botón Aprobar: POST200; autorización de ejecución separada marcada en UI.
- Generar borrador inicia task ace_job_c20cea615e3ef7e85cb22d6d62bc651c887a99b9f17abb18c9e3af2a0f059e8c. Termina completed en backend QA; resultado qa_test_double=true.
- Studio muestra artefacto distinto qa_second_e2af0cdcf215, vinculado al plan/revisión anteriores. Historial conserva también qa_correction_spec_rev_fd8be90a5783, sin reemplazar el original.
- Descarga visible del segundo candidato: song-ai-qa_second_e2af0cdcf215.wav, HTTP200, 192044 bytes, download.failure=null. WAV sintético copiado; misma señal, dos artefactos distintos.
- Recarga restaura Studio, task seleccionada y revisión confirmada.

El harness inicialmente esperaba /ace-candidates/jobs; la ruta real es /ace-candidates. La espera agotó tiempo aunque el job ya había terminado; se comprobó task/resultado/descarga sin repetir la generación. No contabilizar ese timeout como fallo del producto.

## Ajuste de mensajes

La aprobación del plan todavía anunciaba un sample representativo pendiente y el bloque de copia de sample insinuaba que habilitaba producción final. Ambos textos ahora explican que el sample es opcional y la evaluación del audio es independiente. Build Vite aprobado; cambio de texto sin repetición de suites completas.

## Gate

Tramo ligero de corrección → guardado → confirmación → nuevo plan → aprobación → job simulado → segundo artefacto/descarga/recarga comprobado por UI/backend. No acredita recorrido inicial desde idea, motor real, calidad musical o escucha. S06-06/S10-07 mantienen verificación parcial por su evidencia real pendiente; global89,9%. No nuevas canciones de producción ni cambios a configuración Vulkan; sin commit/push. ACE-Step continúa al final de verificación.
