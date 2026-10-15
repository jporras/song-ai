# Lote real Gemma/Qwen — 2026-10-09

SQLite QA qa_consolidation_final_20261007, set-20260601011613100132. Providers reales mediante registry/orquestador con perfiles Vulkan existentes. No ACE-Step, audio nuevo ni cambios a Isabella/Alma de producción.

## Gemma

Dos solicitudes reales completadas con mode=llama_cpp:

- Mejorar sección de una línea totalmente protegida: «Alma sonríe al despertar.» permanece literal.
- Acortar sección QA de tres líneas, con primera y última protegidas: ambas permanecen literales; la línea intermedia también permanece. No afirmar que Gemma acortó o mejoró esa sección.

En ambos casos la ficha persistida permanece sin cambios durante la inferencia y los datos QA originales se restauran tras la preparación de los casos. Duraciones totales de operación: 180.81 y 79.5 segundos, incluyen intento de revisión Qwen; no son latencias aisladas de Gemma. Evidencia gemma_lock_batch_20261009_case1.json, case2.json y gemma_batch_summary_20261009.json en .playwright-mcp.

S05-02: V0.5→1 por ejecución real de escenarios adicionales y líneas protegidas. Cierre limitado a este entregable; no prueba obediencia universal ni utilidad creativa de todas las respuestas.

## Qwen: regresión abierta

La revisión técnica de los dos casos no ejecutó correctamente el provider. Tasks task_2738312e1054 y task_b6c189173446 registran mock_handoff_after_provider_error, provider_executed=false. Errores 10054 (conexión interrumpida) y 10061 (servidor ausente). No se cuentan como revisión real aprobada aunque la task termine completed con fallback.

Reinicio con script administrado y perfil Vulkan existente: task_da630fc19542 vuelve a fallar 10054, 68.44 s. Comprobación aislada después de cerrar solo procesos administrados del proyecto y cargar Qwen sin Gemma: primer intento durante carga responde 503 (guardado aparte); esperado health200, task_0e2b56dbac74 vuelve a fallar 10054 en 60.59 s. Log muestra prompt de 6874 tokens y último checkpoint de prefill en 2048. No hay evidencia suficiente para atribuir la causa a memoria, GPU, driver o tamaño de contexto. Aislar Gemma no resolvió el fallo.

Se solicita restaurar ambos modelos con start-local-llms.ps1 y los mismos perfiles al terminar; health no demuestra que esta solicitud larga funcione. S05-03: V1→0.5, reabierto por fallo actual del provider; se conserva evidencia real histórica y se añaden estos fallos. Global permanece89.9%: mejora de Gemma compensada por regresión de Qwen. No inflar avance contando fallback.

## Harness y siguiente tarea

Caso1 guardó resultado y restauró QA antes de fallar la impresión cp1252 de un carácter Unicode; usar salida ensure_ascii para consola. Primera preparación caso2 rechazó editor/secciones desincronizados antes de inferencia; corregida la preparación sin cambiar validación del producto. No repetir esos intentos como inferencias.

Pendiente prioritario: diagnosticar caída de Qwen en la revisión de contexto largo, corregir su ejecución sin sustituirla silenciosamente por mock y repetir únicamente esa revisión. Propuestas siguen sin guardar. Audio real queda para el último bloque. Sin commit/push.
