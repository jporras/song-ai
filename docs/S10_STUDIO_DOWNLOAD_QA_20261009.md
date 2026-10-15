# S10: descarga y resumen de Studio — 2026-10-09

## Implementacion y evidencia

- Descarga del candidato mediante la ruta de audio y checksum existentes: HTTP 200, Content-Disposition attachment, nombre song-ai-qa_audio.wav, 192044 bytes RIFF y descarga Playwright sin fallo.
- Checksum incorrecto y proyecto ajeno rechazados con HTTP 400.
- Resumen de entrega incluye candidato disponible/en generacion; accion enfoca Studio. Sin candidato/sample dirige a revisar definicion, sin exigir sample.
- Playwright: foco Studio correcto, descarga visible y sin overflow a 390/768/1440 px; siguiente accion sin sample disponible.
- 57 pruebas frontend y build aprobados.

## Limites

Base SQLite QA aislada data/qa_studio_download_20261009; WAV sintetico de dos segundos, no inferencia ni escucha musical. Proyecto/set y seleccion de Studio preparados en el proxy Vue para aislar las superficies; no acredita navegacion completa desde Biblioteca. Un primer intento de harness uso forma incorrecta de activeProject; corregido a activeProject.set.set_id, sin cambios de producto por ese error. No se modifica Isabella ni Alma ni su aceptacion. Servidor QA y navegador cerrados.

S10-07 permanece D0.5/V0.5: quedan recorrido integrado desde idea, correccion y descarga de resultado real. Avance D/V 88.9%, sin transicion de estado por este subbloque.
