# Cancelación y handoff reales — 2026-10-09

## Ensayo

Script `scripts/verify_real_audio_cancellation.py`; runner LocalAudioProcessService real, monitor/guards activos, pesos Turbo/XPU cargados. Copia de caption/letra aceptados de Isabella,120s/8pasos; salida QA aislada sin publicar candidato ni modificar proyecto original. La comprobación espera diagnóstico pipeline_loaded y levanta AudioCancelled. No se afirma fidelidad USER de todos los parámetros de este harness: ese criterio pertenece al runner compilado/request yS06-05.

Intento `data/qa_real_cancel_20261009/1791602127219395700`: resultado cancelled_after_real_load, diagnóstico pipeline_loaded, sin WAV. Worker14108 terminado; comprobación física psutil no encuentra PID. Antes8007MB disponibles, después del cierre7567MB. Log confirma APIreal/XPU y carga de modelos.

El monitor lanzó restauración administrada, pero start-local-llms devuelve antes de completar warmup. Resultado inicial registró health unavailable; posteriormente Gemma200/Qwen503 y finalmente ambos200. El harness ahora espera readiness con plazo90s por servidor; no hace una segunda carga ACE para comprobar este cambio del harness.

## Recuperación verificada

`recovery_verified.json`: worker_terminated true. Llamadas reales /completion con máximo8tokens y temperatura0: GemmaHTTP200/7tokens/1,34s; QwenHTTP200/8tokens/1,66s. Qwen no siguió el texto exacto LISTO en este probe corto; no se acredita obediencia ni calidad musical, solo ejecución del backend restaurado. Sus ensayos de steering/fidelidad permanecen enS05.

RAM disponible310MB después de cargar ambos modelos y ejecutar probes: no iniciar otro audio sin liberar otra vez los modelos. Memoria compartida no suma reserva independiente. No se cerraron otras aplicaciones.

## Cierre de entregables

S04-02 V0,5→1: evidencia previa jobs/SQLite/cancelación tardía más cancelación física con pesos cargados/hijo terminado/sin WAV. S04-03 V0,5→1: cierre administrado de texto, carga ACE, cancelación/limpieza, restauración real y probes reales después del handoff. No equivale a ejecutar los otros cinco modos ni validar todos los parámetros. Aceptación sigue0/fuera deD/V.

Gemma/Qwen quedan activos con perfiles Vulkan vigentes. Próximo caso: ruta alto nivel sin LM, después Cover/Repaint y modosBase.
