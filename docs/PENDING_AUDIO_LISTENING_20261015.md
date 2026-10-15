# Escucha pendiente de candidatos reales — 2026-10-15

Los cinco WAV de abajo existen en copias QA y tienen integridad técnica documentada. Cada uno dura 15 segundos. Escucharlos completos y anotar observaciones por modo permite completar la evaluación perceptual pendiente; la existencia del archivo o su checksum no acreditan calidad ni aceptación. No modificar los originales ni asociar estas decisiones técnicas QA con Isabella.

| ID | Modo y pregunta de escucha | Archivo | Evidencia técnica |
| --- | --- | --- | --- |
| S10-02 | Cover: ¿conserva estructura reconocible y aplica el cambio de estilo solicitado? Comparar con la fuente. | `data/qa_high_level_1791602787119137000/projects/song_d0d582e3925a/candidates/ace_candidate_1ff6158218684958be16fdcb13a9e08e/candidate.wav` | `REAL_COVER_AUDIO_20261009.md` |
| S10-03 | Repaint: ¿son continuas las transiciones en 5 s y 10 s y el tramo editado responde a la intención? Comparar con la fuente. | `data/qa_high_level_1791603039769048600/projects/song_d0d582e3925a/candidates/ace_candidate_85bc859f7ce94f5f87429c27c6968a81/candidate.wav` | `REAL_REPAINT_AUDIO_20261009.md` |
| S10-04 | Lego: ¿se oye guitarra útil en contexto y son naturales las transiciones? | `data/qa_high_level_1791603499514019000/projects/song_d0d582e3925a/candidates/ace_candidate_74863b8767bd4b5c930bb9d7d6e67469/candidate.wav` | `REAL_LEGO_AUDIO_20261009.md` |
| S10-05 | Extract: ¿la voz aislada es inteligible y son aceptables nivel y fugas instrumentales? Escuchar con volumen prudente: RMS medido −40,6 dBFS. | `data/qa_high_level_1791603931010074600/projects/song_d0d582e3925a/candidates/ace_candidate_984ddc6ab856491ca8d1d67dee50aba8/candidate.wav` | `REAL_EXTRACT_AUDIO_20261009.md` |
| S10-06 | Complete: ¿hay batería y es coherente con el arreglo de la fuente? | `data/qa_high_level_1791604384966484400/projects/song_d0d582e3925a/candidates/ace_candidate_05f10a16632e49f7937ec76e7698eb44/candidate.wav` | `REAL_COMPLETE_AUDIO_20261009.md` |

Fuente común: recorte PCM de 15 s de Isabella, registrado en `data/runtime/isabella_qa_15s.json`. Anotar para cada ID quién escuchó, fecha, archivo y checksum consultados, reproducción completa sí/no, observaciones concretas y decisión explícita: cumple / requiere corrección / no evaluado. La evaluación del resultado QA es distinta de aprobar una canción final para un usuario.

S01-03 ya tiene un sample real QA con correspondencia técnica al plan, documentado en `REAL_SAMPLE_CORRESPONDENCE_20261015.md`; su representatividad audible sigue pendiente de aceptación. S04-04 requiere preferencia auditiva A/B. S10-07 requiere el recorrido integrado desde idea hasta descarga con un resultado real y corrección; la reproducción/descarga aislada ya está documentada. S10-08 requiere participantes amateur según `AMATEUR_PILOT_PROTOCOL.md`. La ruta LM opcional y parámetros efectivos siguen en S00-04/S06-05. Mantener esos IDs parciales hasta tener su evidencia propia.
