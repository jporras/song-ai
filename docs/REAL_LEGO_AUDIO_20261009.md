# Lego real — 2026-10-09

QA1791603499514019000; plan `ace_plan_c468153aa9364d83a97ef5d00696c80f`, revisión `spec_rev_1262e38119fe`. Base/direct/CPU32pasos. Fuente: recorte técnico15s Isabella, intervalo5–10s y pista guitar; instrucción instalada `Generate the guitar track based on the audio context:`. Caso técnico sobre copia QA, no nueva intención confirmada de Isabella ni canción aceptada.

Job completed; artefacto `ace_candidate_74863b8767bd4b5c930bb9d7d6e67469`. WAV15s/48kHz/estéreo/PCM16/2880044bytes; SHA256 `1df3da93f23c99cd11155ef6ae15e61ec9ea1a8705a63766a376f1a8143055f8`. Señal no silenciosa, cero muestras a escala máxima; pico−9.475dBFS, RMS−24.236dBFS. Resultado y `signal_postflight.json` conservados en directorio QA.

Runtime reported_completion: configuración coincidente, CPU32pasos; input_observation matched a nivelwrapper, sin atribuir observación independiente del motor. Runner388.5s, mínimo RAM0MB, pico100%, swap máximo13318MB. No ampliar concurrencia; ejecución Base exitosa bajo presión de memoria no demuestra margen operativo estable.

Comparación PCM antes/seleccionado/después: identidad99.5031%/0.0369%/99.5006%, diferencia RMS relativa0.001726/0.052276/0.001672. Esto verifica cambio de señal aproximadamente localizado, no presencia efectiva de guitarra ni fidelidad/coherencia por escucha. S10-04 V0→0.5; escucha pendiente, aceptación separada.

Tras medición/checksum/señal correctos, el lote inició Extract/vocals en QA1791603931010074600, plan `ace_plan_3b8dd06166ba4aec8d780cef25107a49`. Complete/drums espera su resultado. Sin cargas concurrentes; originales intactos.

Descarga real ASGI comprobada con `scripts/verify_real_candidate_download.py`: HTTP200,2880044bytes idénticos porSHA256,Content-Disposition attachment/audio-wav; checksumincorrecto rechazadoHTTP400. Informe `download_postflight.json` en la QA. No prueba navegador ni registra escucha/aceptación; cierre integrado sigue pendiente.
