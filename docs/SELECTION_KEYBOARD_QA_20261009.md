# Selección y teclado — 2026-10-09

## Correcciones S06-01

Instrumentos e inspiraciones declaran aria-pressed y muestran texto seleccionado. Pistas MIDI, silencio/solo instrumental y activación de capas vocales declaran su estado pulsado. La composición tiene botones Mover antes/Mover después/Eliminar con nombre de sección y límites deshabilitados. El error de guardado recibe foco después del render, con role alert y tabindex -1.

## Verificación

Vite build aprobado. Playwright MCP con SQLite QA aislado: Enter en instrumento cambió aria-pressed true→false y segundo Enter restauró selección; Calidez101 produjo foco en phase-save-error con mensaje comprensible, después se restauró63 y guardó HTTP200. Composición: Enter movió primera sección a segunda posición, botón de regreso restauró orden, límite inicial deshabilitado; guardadoHTTP200. Reflow320/768/1440 sin desbordamiento.

El primer selector del harness de instrumentos no existía y agotó timeout; el selector de details/chip-grid permitió completar el caso. No se atribuye ese timeout al producto. Sin inferencia/audio; navegador y servidor cerrados.

Alcance: teclado/estado/foco de superficies observadas. No prueba de lector de pantalla ni certificación WCAG. S06-01 conserva verificación parcial por revisión global de contraste/estados aún pendiente; aceptación amateur fuera de D/V.
