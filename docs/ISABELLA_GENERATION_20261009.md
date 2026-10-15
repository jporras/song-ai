# Isabella — generación real solicitada (2026-10-09)

## Preparación

Proyecto productivo song_2ea83a928856, set set-20260531133207958397. Letra existente de 344 caracteres guardada desde las tres secciones persistidas; se elimina solo whitespace terminal por sección para normalizar Markdown. Texto cantado e intención instrumental/vocal/lírica conservados. Se verificó identidad de todos los campos creativos públicos antes/después. SQLite ahora incluye _lyrics_document; no se sobrescriben originales rescatados.

Solicitud del usuario: generar Isabella. Ficha confirmada en revisión 3, después de incorporar letra en revisión 2. Plan ace_plan_5c4e50ea553a4f9eb87f7f102732096e aprobado con letra existente; hash 190a78980dd90aebbb1bcaccd2b9cac17dd9db7eefa8af080fa11cd0dca64b4d. Duración de ficha 120 s, text2music, Turbo/direct, voz femenina cálida. Sin aprobación creativa nueva inferida de un modelo ni aprobación de audio.

## Recursos

PyTorch 2.9.1+xpu detecta Intel(R) Graphics por Level-Zero, GPU disponible. API XPU informa 7955 MB de memoria total direccionable. La memoria gráfica compartida de iGPU no es una reserva independiente que se sume a la RAM; véase https://www.intel.com/content/www/us/en/support/articles/000020962/graphics.html . RAM libre medida 8,4 GiB inicialmente y 10,16 GiB en consulta posterior; presupuesto conservador de pesos+reserva 7049 MiB. No equivale a working set medido ni prueba de calidad.

## Ejecución

Primer job ace_job_8bd407df21ca4a53a995455fd7ae7318 falló antes de cargar audio por Get-CimInstance AccessDenied dentro del entorno restringido. No fallo del modelo. Un error del harness posterior al POST consultó status_code como función; POST sí había devuelto 200 y se comprobó la tarea sin duplicarlo.

Se cerró servidor restringido y se ejecutó cierre verificado de modelos y API con permisos aprobados. API local persistente http://127.0.0.1:8017, autostart LLM/bootstrap desactivados; monitor y guards reales conservados. Segundo job ace_job_5bb476f652cc4f5a9835c918bceb9b54 recibido HTTP 200, estado running/progress 5. Carpeta candidates/ace_candidate_1e794dcb99dc4591b673eec8f423db74.

Ruta de candidatos de la aplicación produce audio de duración completa sin sample previo; no se presenta el candidato como exportación final aceptada. No se modifica el gate legado de mastering/export en esta ejecución. Estado pendiente de diagnóstico, integridad técnica, escucha completa y aceptación. El servidor queda en ejecución para conservar worker; no se anuncia archivo generado antes de finalizar.

## Última comprobación antes de dejar el worker activo

Job running. generation.log confirma handler real y selección requested=xpu active=xpu, torch=2.9.1+xpu. Primeros recursos: aproximadamente 9,6–9,9 GiB libres; sin error registrado en esa consulta. Selección XPU comprobada, carga completa/inferencia/archivo final todavía pendientes.

## Resultado comprobado

Task completed/progress 100. Archivo candidate.wav de 120,0 s, PCM 16 bits, 48 kHz, estéreo, 23.040.044 bytes. SHA256 coincide con SQLite: 5feddd75d5c8680cf594ece9f047febce256082c77c121db5a4212db7f20ab0c. Se decodificaron todos los frames y hay señal no silenciosa. Métricas de amplitud son comprobaciones técnicas, no escucha ni garantía de voz/fidelidad.

Diagnóstico reporta Turbo, API directa sin LM, ocho pasos, active_device=xpu sin fallback. Wrapper terminó en 328,1 s (5 min 28 s). Hubo presión fuerte de memoria: mínimo 16 MiB libres, RAM 99,9%, swap pico 3933 MiB; terminó y liberó memoria. Presupuesto inicial conservador no predijo el pico real; registrar para optimización posterior sin alterar la intención musical.

Pendiente escuchar el audio completo y evaluar letra cantada, voz, instrumentos, fidelidad y aceptación. No se marca aceptación musical ni se reemplazan los finales históricos.

## Aceptación expresa del usuario — 2026-10-09

El usuario acepta la canción actual y difiere los ajustes mínimos de calidad. Opinión vigente `accepted` registrada en SQLite, evento `event_428c59b47301`, vinculada al job, artefacto, checksum, plan y revisión de ficha descritos arriba. El feedback previo de voz sintética en la vocal “u” alrededor de 20 s permanece en el historial y como mejora posterior; no condiciona esta aceptación.

S10-01 se cierra para el caso real text2music Isabella: ejecución e integridad comprobadas, escucha reportada y aceptación expresa. Esta decisión no afirma análisis objetivo completo de letra/BPM/tonalidad, ni acredita cover/repaint/modos Base, piloto de usabilidad o exportación final del recorrido. La API conserva `final_quality_verified=false` porque la aceptación de escucha y la verificación técnica exhaustiva son estados separados. Los párrafos anteriores documentan el estado antes de esta aceptación.
