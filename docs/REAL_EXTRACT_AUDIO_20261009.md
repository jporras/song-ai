# Extract real — 2026-10-09

QA1791603931010074600, plan `ace_plan_3b8dd06166ba4aec8d780cef25107a49`, revisión `spec_rev_bf8cadbf38aa`. Base/direct/CPU32pasos; fuente PCM15s de Isabella, pista vocals, instrucción instalada `Extract the vocals track from the audio:`. Escenario QA aislado, no confirmación creativa del proyecto original. La procedencia heredada del fixture no prueba aprobación USER de los valores técnicos; corrección posterior documentada en README.

Job completed, artefacto `ace_candidate_984ddc6ab856491ca8d1d67dee50aba8`. WAV15s/48kHz/estéreo/PCM16/2880044bytes, SHA256 `1d66e6b8e016083a2e204ad2c4fa5e354a26d7a73963fba64ffafd15428142d2`. Runtime reported_completion, configuración coincidente, CPU32pasos, input_observation matched a nivelwrapper; no observación independiente del motor.

Informe `signal_postflight.json`: no silencio digital, cero muestras a escala máxima, pico−23.086dBFS, RMS−40.634dBFS. Nivel de señal bajo: no normalizar ni alterar el original para ocultarlo; comprobar voz útil y fugas de instrumentos por escucha antes de cerrar verificación. Las diferencias PCM en regiones0–5/5–10/10–15 no prueban separación vocal; Extract no solicita una edición localizada.

Runner407.8s, mínimoRAM160MB/pico99%, swapmáximo13993MB. S10-05 V0→0.5; integridad/generación verificadas, evaluación de separación pendiente. No registra aceptación. Tras checksum/señal, Complete/drums comenzó en QA1791604384966484400, plan `ace_plan_bbb7ef0dd8014749b54483ee30e58f41`, revisión `spec_rev_e0d3da171cbc`; difusión iniciada sin cargas simultáneas.
