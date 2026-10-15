# Preparación de Cover/Repaint — 2026-10-09

El harness `scripts/verify_real_high_level_audio.py` admite tareas y API explícitas, fuente, instrucción/pistas y prepare-only. Esta última usa importación, SQLite, compilador, checksums y aprobación QA sin despachar audio. No altera proyectos originales, no representa confirmación creativa del usuario final.

Fuente: WAV real aceptado de Isabella; recorte PCM de los primeros15s, sin remuestreo. Fuente/checksums/transformación registrados en `data/runtime/isabella_qa_15s.json`. No se presenta como sample aprobado ni canción nueva.

- Repaint/direct: plan ace_plan_32dda769d6044fcba4930df3d91f89f5, SHA7ea6065bedf4faf8956227548022aabdf02dd3642df29b431779dff1bb9ffeaf; intervalo5–10s, máscara explicit. Directorio QA1791602643469456000.
- Cover/direct: plan ace_plan_76bd7d735cdd46f0b36a3500f7dd4476, SHA34f36a26d01afd5aa59f03ef6d15ee28ada429ba9ed82249f605288ba757ac7b. Directorio QA1791602662358587500.

Ambos prepared_not_executed: pasan verificación de fuente y compilación real, no acreditan generación ni conservación audible. No hubo solapamiento de cargas: el único job real sigue siendo alto nivel sinLM. El último log de ese job muestra difusión completada y decodificación VAE, aún sin resultado final disponible. Global92,0% sin sumar preparación como modo probado.

## Continuación del lote

Cover/direct iniciado en QA1791602787119137000 (plan ace_plan_c344f17b8035459e9e346917697996dc). Repaint queda secuenciado mediante continue_real_audio_batch.py; no arranca antes del resultado completed deCover, ni si este falla.

Base preparado sin cargar pesos:
- Lego/guitar: plan ace_plan_01f8427f9dda4d51b4c546b6bb698a9d, QA1791602839480317800.
- Extract/vocals: plan ace_plan_3f55d6de643740b8acef20b632a0356f, QA1791602839636954800.
- Complete/drums: plan ace_plan_d2f4fb7060bb4d46b0777bf8b92cd13e, QA1791602840024838700.

Instrucciones corresponden a TASK_INSTRUCTIONS del ACE-Step instalado. Casos técnicosQA, no inferencia de intención ni aceptación de canciones. Global92,4%.
