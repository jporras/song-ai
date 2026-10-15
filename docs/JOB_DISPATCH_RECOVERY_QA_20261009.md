# Jobs: fallo de dispatcher y recuperación — 2026-10-09

## Defecto corregido

Cuando submit fallaba antes de lanzar worker, el job se persistía failed pero su Event de cancelación quedaba retenido en el manager. La rama de error elimina ahora ese token antes de registrar el fallo; no altera intención, plan ni request.

## Verificación agrupada

`python -m unittest tests.test_ace_step_candidate_jobs tests.test_local_audio_process_cleanup`:15 pruebas aprobadas en3,863s, sin fallos/omitidas.

Regresión nueva: fallo de dispatcher no llama generador, job queda failed, tokens vacíos y orquestador sin task de audio activa; reenviar la misma identidad devuelve el intento anterior sin dispatch extra; una acción explícita nueva completa su job y vuelve a liberar tokens.

Lote incluye persistencia/reapertura, aislamiento por proyecto, exclusión de llamadas a Gemma/Qwen durante audio activo, pausa/reanudación por estado SQLite, cancelación pendiente/en ejecución, fallos/reinicio, reproducción con checksum y limpieza de procesos Python reales desechables antes de restaurar modelos. Estos hijos no cargan ACE-Step ni usan GPU.

S04-01 ya cerrado: se fortalece evidencia, sin sumar puntos. S04-02/03 siguen parciales exclusivamente por cancelación con pesos cargados y recuperación/medición física de memoria en lote final. Este lote no acredita esas condiciones. Global90,8%.
