# S06-01: intención emocional accesible — 2026-10-09

Revisión del contrato SONG_BUILDER_UX_ARCHITECTURE_20261007.md: sliders deben contar con campo numérico y escala explicada. Idea tenía cuatro sliders sin alternativa numérica.

## Implementación

emotional_controls.js define las cuatro etiquetas/ayudas y validación frontend. Cada slider tiene campo numérico sincronizado, rango0–100, ayuda visible asociada mediante aria-describedby. Nombre del panel Intención emocional; Sensación cinematográfica aclara el antiguo Cinemático. Valores describen intención creativa, sin prometer un parámetro físico ACE-Step.

savePhaseData bloquea guardar valores no numéricos/no finitos/fuera de rango. SaveMusicSpecPhase aplica el mismo contrato a campos presentes en intent antes de escribir: rechaza booleanos, strings e inválidos. No recorta silenciosamente valores. Campos históricos ausentes siguen permitidos, sin imponer nuevos defaults backend.

## Verificación agrupada

- 18 pruebas test_music_spec_phases aprobadas (45.420s), incluye rechazo sin cambios de ficha y persistencia de extremos0/100 mediante servicio/SQLite.
- 3 pruebas frontend focalizadas aprobadas: controles emocionales y apertura Builder. Build Vite aprobado.
- Playwright QA8024: Calidez numérica63 sincroniza slider63; 101 bloquea guardado con mensaje comprensible; valor63 guardado por PUT fase intent HTTP200 y restaurado con slider63 después de cargar el proyecto.
- Primer chequeo de recarga veía defaults82 antes de terminar carga; comprobado posteriormente con activeProjectId correcto y dato persistido63. No defecto de persistencia atribuido a ese estado inicial.

Solo datos QA alterados, modelos deshabilitados en el servidor, sin audio ni inferencia. S06-01 mantiene verificación parcial por cobertura global restante, sin cierre WCAG/usabilidad. D/V90,5%. No commit/push; servidor/browser cerrados al finalizar.
