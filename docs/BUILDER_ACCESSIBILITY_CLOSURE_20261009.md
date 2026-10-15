# Cierre de verificación S06-01 — 2026-10-09

## Cambios del último lote

Controles HTML conservan semántica y teclado, con indicadores visuales definidos: checkbox/radio y pistas/thumbs de range para Chromium/Firefox. Forced colors vuelve a appearance auto. Casilla24px con etiqueta clicable; rangos44px y alternativa numérica existente. Texto de error del diálogo admite foco programático. Rótulo Borrar proyecto corregido de4,3046:1 a7,0236:1 sobre superficie elevada.

## Evidencia actual del lote

- Vite build aprobado.
- Playwright MCP Chromium: Espacio alterna y restaura casilla; flecha derecha31→32 e izquierda→31; guardado restauradoHTTP200. Captura `../.playwright-mcp/native_controls_20261009.png` inspeccionada: marca y límite de casilla visibles.
- Apariencia explícita none en controles; apariencia auto con forced-colors active. Reglas Firefox definidas pero no se afirma ejecución en Firefox. No hay radio visible en los casos revisados.
- Tres diálogos renderizados con fixtures de UI, cerrados con Escape sin ejecutar eliminación. Texto normal y botones evaluados; único fallo corregido fue eyebrow de eliminación. Fondos elevados opacos: el backdrop no altera su contraste interior.
- CTA Guardar en normal/hover/active/disabled observado después de finalizar transiciones:6,2097/7,9801/4,7616/6,1104:1. Disabled conserva opacity1. Pista contra superficie4,8475:1; thumb/indicador6,2097:1.
- El primer ensayo sirvió el build anterior porque el backend conserva index al arrancar. Se reinició servidor y se verificaron los assets nuevos; no se acreditó esa primera lectura como estilos nuevos. Beforeunload conservó protección de borrador; se aceptó únicamente en QA para recargar.
- Navegador/servidor QA cerrados; sin modelos/audio nuevo ni datos de producción modificados.

## Matriz de cierre acumulada

| Criterio S06-01 | Evidencia |
| --- | --- |
| Shell/recorrido, restauración y separación Studio | BUILDER_BATCH_QA_20261009.md, BUILDER_STUDIO_REGRESSION_20261008.md |
| Reflow320/390/768/1440 y texto200% | ACCESSIBILITY_GROUPED_CHECK_20261009.md, SELECTION_KEYBOARD_QA_20261009.md |
| Labels, ayuda por teclado, estados sin depender del color | SELECTION_KEYBOARD_QA_20261009.md, LIBRARY_FAVORITES_ACCESSIBILITY_20261009.md |
| Sliders/entrada numérica, errores y persistencia | EMOTIONAL_CONTROLS_QA_20261009.md, NUMERIC_DIRECTION_CONTROLS_20261009.md |
| Texto, inputs, bordes y placeholders | BUILDER_ACCESSIBILITY_BATCH_20261009.md, BUILDER_CONTROL_CONTRAST_20261009.md |
| Diálogos, controles nativos y estados CTA | Este documento y evidencia previa Tab/ShiftTab/Escape |
| Estados de generación, corrección, revisión y entrega | BUILDER_ACCESSIBILITY_BATCH_20261009.md, CORRECTION_DELIVERY_PLAYWRIGHT_20261009.md, SECOND_CANDIDATE_QA_20261009.md |

S06-01 V0,5→1: verificación de ingeniería del alcance implementado en Chromium, apoyada en matriz concreta; no se exige recorrer todas las combinaciones posibles para acreditar estos componentes. No certificación WCAG integral, prueba de lector de pantalla, compatibilidad Firefox acreditada ni aceptación amateur. Estas limitaciones se conservan explícitas; el piloto pertenece aS10-08 y aceptación fuera deD/V. Audio/handoffs reales pendientes conservan sus propios entregables y no se cierran aquí.
