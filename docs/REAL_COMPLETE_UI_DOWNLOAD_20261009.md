# Complete real en Studio y descarga — 2026-10-09

Playwright MCP, localhost8025, SQLite QA1791604384966484400; modelos desactivados. Navegación real Biblioteca→Cargar→Production→7.Studio, sin asignar candidato en el proxy Vue. UI recupera job real completed y checksum de Complete.

Reproductor A cargó duración15s, play avanzó a0.708371s, pausedfalse, errornull; pausado después. Esto verifica reproducción del navegador, no escucha musical completa ni aceptación. Descarga mediante enlace visible: evento download sin fallo, nombre `song-ai-ace_candidate_05f10a16632e49f7937ec76e7698eb44.wav`. Copia `.playwright-mcp/complete-real-download.wav`, SHA256 `d2ef24dd0a34898a982abf491ee0d37f43d20644bd1bb7464d8dba04e0e434f0`, idéntico al artefacto.

Fallo de producto encontrado: copia estática «ejecución pendiente» incluso con jobcompleted del mismo plan. Corregida: si coincide planID y jobcompleted, muestra candidato generado/escucha pendiente; si está activo, informa generación en curso; otros casos permiten iniciar generación. No usa el estado de un candidato de otro plan. Build Vite aprobado, comprobación Playwright tras reiniciar servidor y recargar.

No acredita idea→corrección→resultado integrado, comparación A/B ni exportaciones finales MP3/FLAC/ZIP. S01-04/S04-04/S10-07 conservan pendientes, sin aumentar porcentaje por este subbloque. Originales intactos y sin opinión/aceptación guardadas.
