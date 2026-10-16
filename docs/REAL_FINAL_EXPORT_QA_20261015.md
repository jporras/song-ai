# S01-04 — generación final real y límite de exportación QA

Proyecto aislado `data/qa_high_level_1791602467245496700`, canción `song_d0d582e3925a`, set `qa-builder-batch-set`. El plan `ace_plan_2cb5913a56a24c0e8218c960d564178c` estaba aprobado como escenario técnico QA y la letra del archivo coincidía con el request. Esta autorización técnica no equivale a aprobación creativa de una persona ni a aceptación del audio.

Preflight Turbo sin LM: presupuesto de pesos y reserva 7049 MB; RAM disponible previa ~8945 MB. Gemma y Qwen estaban cerrados. La primera generación ACE-Step produjo un WAV real, pero la conversión se detuvo porque `ffmpeg` instalado en `data/tools/ffmpeg/bin` no estaba en el PATH. Se añadió resolución del binario administrado además del PATH. La segunda ejecución completa produjo y registró WAV/MP3/FLAC; tardó 121,11 s. El runner restauró los servidores LLM y se cerraron después con `stop-local-llms.ps1`.

| Tipo | Tamaño | SHA256 | Inspección `ffprobe` |
| --- | ---: | --- | --- |
| WAV | 2880044 bytes | `d21dcbb6288028edf5aa3db590de98c483e6140df7a04d2ed1135100b2761689` | PCM16, 48 kHz, estéreo, 15 s |
| MP3 | 240621 bytes | `ff113c336d4163a0e9919517f774512f2f53d59c5732a7bb0bd1bde02d0c2543` | MP3, 48 kHz, estéreo, 15 s |
| FLAC | 1031110 bytes | `7f5e5adaf35fc82fc0c71ed1c572d69bd6070f7d7f1aab56383dd2a6cb7c394c` | FLAC, 48 kHz, estéreo, 15 s |

Los tres artefactos tienen `artifact_status=GENERATED` tras verificación de checksum y `professional_artifact_download_file` devuelve archivo, nombre y MIME correctos. Informe estructurado local: `data/qa_high_level_1791602467245496700/final_files_verified_20261015.json` (no versionado por contener rutas y audio QA).

La exportación integrada **no terminó**. `export_professional_song` rechazó el proyecto porque faltan registros de `song_spec`, `lyrics_json`, `lyrics_approved_json`, `music_plan_json` y `midi`; la copia QA original solo registraba el candidato ACE-Step. Además, `lyrics_approved.json` conserva `status=pending_review`, por lo que no se debe registrar como revisión aprobada ni afirmar que el manifest/ZIP final está listo. Se requiere un escenario QA completo con esos pasos verificados. La descarga individual de los tres archivos reales está comprobada; manifest, ZIP y descarga final integrada siguen pendientes. No hubo escucha ni aceptación.

Regresión posterior: 377 pruebas Python ejecutadas, 372 aprobadas, 5 omitidas, 0 fallidas, 116,328 s. S01-04 permanece V0.5; no cambia el 97,9 % D/V.

## Continuación: exportación integrada desde plan ACE-Step vigente

El bloqueo anterior describía el exportador heredado. Para la ruta ACE-Step, el exportador ahora comprueba que el WAV final corresponda al último plan aprobado para esta QA, su hash y la revisión actual de MusicSpec. Regenera `song_spec.json` desde SQLite, coteja `lyrics.md` con la letra del plan y registra `ace_plan.json`; no exige MIDI ni convierte `lyrics_approved.json` con `pending_review` en una aprobación ficticia. El exportador conserva el contrato heredado para generaciones que no proceden de un plan ACE-Step. Los artefactos copiados de otro proyecto no entran en el ZIP.

Se reintentó `export_professional_song` en la misma QA aislada: `export_ready=true`, manifest registrado y ZIP íntegro con `song_spec.json`, `ace_plan.json`, `lyrics.md`, WAV, MP3, FLAC y el candidato de procedencia. `scripts/verify_real_final_export.py` abrió el ZIP, verificó su CRC y sus miembros y descargó por ASGI MP3, FLAC y ZIP: HTTP 200, `attachment`, MIME correcto y SHA256 idéntico al de SQLite. El ZIP tiene 5 789 505 bytes y SHA256 `336ccc606312c169525c6ac1eaf147c58c2529f7abb047ac74db233eed420b51`. El informe reproducible está en `data/qa_high_level_1791602467245496700/final_export_postflight_20261015.json`.

Esto cierra la verificación técnica de S01-04. `audio_acceptance_recorded=false`: quedan para aceptación la escucha completa y la decisión del usuario. No se atribuye aprobación creativa humana a la aprobación técnica del plan QA.

Regresión final de este bloque: `python -m unittest discover -s tests -p 'test_*.py' -q` con 379 ejecutadas, 374 aprobadas, 5 omitidas y 0 fallidas en 253,055 s. Incluye dos pruebas nuevas para requisitos de exportación ACE-Step y exclusión de artefactos ajenos. `compileall` y `git diff --check` correctos.
