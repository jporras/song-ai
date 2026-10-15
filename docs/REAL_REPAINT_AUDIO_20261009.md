# Repaint real — 2026-10-09

QA aislada `data/qa_high_level_1791603039769048600`; plan `ace_plan_55d1902f0cce4f7eb9836edcaecc8ab6`, revisión `spec_rev_ee0805a6a36e`. Fuente: recorte PCM de Isabella aceptada; original sin cambios. Turbo/direct/XPU, 8 pasos, intervalo 5–10s, máscara explicit. Job completed; artefacto `ace_candidate_85bc859f7ce94f5f87429c27c6968a81`.

WAV 15s/48kHz/estéreo/PCM16/2880044bytes. SHA256 `1859ada043cef2a152d1e5fe30dec467739d7f8a3c04d696133e2a5b1d83123a`. Señal no silenciosa, cero muestras a escala máxima; pico −9.475dBFS, RMS −24.577dBFS. Informe reproducible `signal_postflight.json` en el directorio QA, generado con `scripts/measure_real_audio_result.py`.

Identidad PCM por región: antes 99.5029%, tramo seleccionado 0.2073%, después 99.5063%. Diferencia RMS relativa a escala máxima: 0.001187/0.045199/0.001183. El motor instalado aplica splice de waveform salvo modo aggressive y admite crossfade en límites. Estos valores acreditan modificación localizada aproximada; no prueban calidad perceptual, ausencia de clicks ni que todas las diferencias externas correspondan exclusivamente al crossfade.

Runner 211.8s; mínimo RAM 247MB, pico 98.4%, swap máximo 6942MB. Ejecución serializada. S10-03 V0→0.5: generación/integridad y comparación por regiones; escucha de transiciones/fidelidad pendiente. Aceptación permanece separada.

## Conservación fuera de los bordes

Comparación adicional de las regiones 0–4.95s y 10.05–15s: 100% de muestras PCM idénticas y diferencias RMS/máxima cero en ambas. Informe `repaint_boundary_comparison.json` en la misma QA. Todas las diferencias externas al intervalo solicitado quedan dentro de un margen de 50ms alrededor de cada borde; este margen es el usado para medir, no una afirmación del tamaño exacto de crossfade ni un nuevo parámetro aprobado. Sigue pendiente escuchar las transiciones y evaluar la intención musical. No se incrementa V por esta medición adicional.
