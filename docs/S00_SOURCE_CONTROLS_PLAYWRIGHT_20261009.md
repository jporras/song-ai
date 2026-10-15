# S00: fuentes, intervalos y pistas en UI — 2026-10-09

QA song_2761b70727d6 en SQLite aislada data/qa_user_controls_20261009. Seleccion inicial mediante Vue; controles reales para importar/seleccionar/editar/guardar. WAV sintetico 2s/48000Hz/mono/PCM16, sin inferencia.

## Evidencia

- Importacion desde file input, permiso explicitamente marcado; original 192044 bytes, SHA256 6b27d46efff26ae0d2cb1ddaf760cde75bb5c5cb9ecbe4135bda31edd3543abf. Importar no selecciona fuente ni referencia automaticamente.
- Fuente y referencia seleccionadas source_b0061062662d4b8b8676dd00c337a5b8; guardado identifica IDs USER, rutas resueltas SYSTEM, preview registra checksum verificado para ambas.
- Repaint: 0.5→1.5 segundos, valores preservados y chunk_mask_mode explicit declarado SYSTEM. Confirmacion por boton y preview API HTTP200.
- Cover: conservacion0.75 guardada y confirmada (revisiones4/5). Compilacion de snapshot historico confirmado conserva0.75; evidencia S00_SOURCE_CONTROLS_COVER_20261009.json. No es plan vigente ni ejecucion.
- Lego: seleccion guitar y preparacion explicita de instruccion guitar. Extract conserva guitar. Complete seleccion bass/guitar; select multiple devuelve orden de opciones bass,guitar y boton prepara bass, guitar. PATCH y preview preservan ese orden; no promesa de prioridad musical del orden. Confirmaciones de estas tres por API, no boton.
- UI hace guardado antes de confirmacion; preview es consulta API, no ejecucion. Sin nueva letra de editor: argumento Letra QA no confirmado.

## Harness y limites

Una respuesta importada no se pudo releer desde cache de inspector; artefacto/evidencia constatados en estado y SQLite. Primer loop encontro limpieza de estado de proyecto no vinculado tras confirmacion: aislado recargando entre casos. Segundo intento Cover sin cambios no emitio PATCH. Ultimo guardado Cover0.65 uso revision anterior tras confirmacion API y fue rechazado HTTP400; DB mantiene revision11 Complete. No se presenta como defecto de producto. Servidor QA y navegador cerrados.

Faltan selector LM cambiado, editor/locks de letra y chat, condiciones adicionales y recorrido integral. S00-03 sigue parcial; no generacion real de estos modos ni calidad musical acreditadas.
