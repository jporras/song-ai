# S00: editor de letra y preview — 2026-10-09

QA SQLite data/qa_lyrics_controls_20261009, set qa-lyrics-set con tres assets mock, song_721d011fa67f. Seleccion inicial mediante loadProject del proxy Vue; editor, proteccion, guardado y navegacion a Revisar/confirmacion mediante controles visibles.

Texto inicial guardado: José, quédate aquí. / Mi canción conserva tu intención. Proteccion linea0. PUT fase lyrics conserva texto/proteccion; recarga restaura ambas. Intento Otra voz. en linea0 rechazado por UI y restaura texto con aviso de desbloquear. Otra linea editada a Tu melodía guarda mi intención.; PUT200. Navegacion 5.Revisar y confirmacion por boton HTTP200. Preview API conserva markdown literal con origen _lyrics_document.markdown y transformacion section_text_to_markdown_v1. Otra letra rechazada400.

Detectado lyrics_source erroneo preview_request_unconfirmed aun cuando texto procedia de MusicSpec confirmado. Corregido a confirmed_music_spec_document para ese caso; argumento externo sigue preview_request_unconfirmed. lyrics_confirmation del plan sigue requerido; no equivale a aprobar audio ni ejecutar.

Harness: primera espera usaba POST en vez del PUT real, ajustada sin cambiar producto. Assets mock, sin inferencia ni audio. Servidor QA y navegador cerrados. S00-03 permanece parcial por chat y condiciones adicionales. D/V88.9%.

Lote posterior a correccion: 33 pruebas backend aprobadas.
