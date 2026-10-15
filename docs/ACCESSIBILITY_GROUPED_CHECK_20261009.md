# Comprobación agrupada de accesibilidad — 2026-10-09

Playwright MCP sobre backend/SQLite QA8024 existente, sin nuevos proyectos, modelos ni audio.

- Siete pasos: 106/39/61/45/51/51/50 controles visibles observados. Escáner DOM no detecta controles sin nombre por label, aria-label/labelledby, texto o title. No equivalente a cálculo completo del nombre accesible por tecnología asistiva; conteos cambian con paneles abiertos y carga de datos.
- Texto de main y asistente ampliado 200% a viewport768×900, siete pasos, sin desbordamiento horizontal. Capturar tamaños computados antes de aplicar ampliación para no multiplicar por herencia. El primer ensayo lo hacía secuencialmente y produjo tamaños artificialmente exponenciales; corregido el harness, sin cambios CSS del producto.
- Seis estados de GenerationStatus con job simulado y restauración del valor original: 6/6/5/5/6/5 textos/acciones examinados, ninguno por debajo de4.5:1 contra el fondo del panel. aria-live polite presente en todos; progreso0 con label comprensible, independiente de calidad.
- Evidencia anterior reutilizada: siete pasos/reflow/recarga/ayuda, tres diálogos, favoritos, estados y opinión/corrección/descargas. No repetir suites completas sin cambio funcional.

S06-01 mantiene V0.5: este lote cubre texto/control/progreso en superficies observadas, no todos los estados posibles de formularios, contraste gráfico, placeholders, overlays ni lector de pantalla. No certificación WCAG o aceptación amateur. Global90,5%, sin cambio de estados ni código de producto. No generacion real de audio ni commit/push. Servidor y browser QA cerrados.
