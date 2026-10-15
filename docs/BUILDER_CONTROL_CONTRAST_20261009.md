# Contraste de controles del Builder — 2026-10-09

## Matriz agrupada Playwright MCP

SQLite QA aislado8024; sin modelos ni audio. Script reproducible: `scripts/playwright_builder_control_contrast.js`. Composición alfa de fondos de ancestros y luminancia sRGB; borde contra fondo interior y exterior, texto y placeholder contra fondo compuesto.

| Superficie | Campos examinados | Fallos |
| --- | ---: | ---: |
| Idea |13|0|
| Sonido |12|0|
| Composición |28|0|
| Letra |11|0|
| Revisar, configuración abierta |43|0|
| Generar |2|0|
| Studio |2|0|
| Voz |22|0|
| Biblioteca |8|0|

141 evaluaciones, con repeticiones del asistente; no son campos únicos. Mínimos: borde4,5456:1 (objetivo3), texto15,0571:1 (objetivo4,5), placeholders7,2405:1 (objetivo4,5). Los primeros ensayos de producción solo cubrían el asistente por restauración asíncrona/panel cerrado; se corrigió el harness esperando el proyecto de producción y abriendo configuración, y se repitió la matriz.

CTA Guardar observado en normal, hover y foco por teclado (Tab/Shift+Tab). No se ejecutó generación.

## Límites concretos restantes de S06-01

Este lote cierra campos, bordes y placeholders renderizados de la matriz. La evidencia anterior cubre texto, navegación, reflow, errores, selección y diálogos por teclado. Para el cierre de verificación visual aún quedan controles nativos checkbox/radio/range (no se calculan desde borderColor), contraste compuesto de diálogos y estados active/disabled. No volver a abrir los campos ya cubiertos sin regresión concreta. El script no calcula gradientes/imágenes, opacidad global ni conformidad WCAG integral. La evaluación con personas amateur se mantiene en aceptación, fuera del porcentaje D/V.

Servidor y navegador cerrados. S06-01 V0,5; global90,5%.
