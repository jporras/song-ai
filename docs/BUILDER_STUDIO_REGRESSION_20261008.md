# Regresión Builder/Studio — 2026-10-08

## Evidencia

- Suite frontend: 46 pruebas aprobadas, cero fallos/cancelaciones.
- Playwright MCP sobre servidor QA y datos temporales: pending/running/cancelling/cancelled/failed/completed; cancelar disponible solo pending/running; progreso numérico cero visible; error de task visible.
- Opinión histórica visible cuando audio/configuración no vigentes.
- Solicitud de cambios exige notas: required true y checkValidity false con texto vacío.
- Archivo deliberadamente inválido: error español accionable, reintento habilitado y reproductor conservado. Fallo de presentación detectado y corregido en audio_waveform.js.
- Build final aprobado. No ejecución de ACE-Step ni evaluación de calidad de música.

## Límite y siguiente pendiente

Esta matriz complementa los ensayos anteriores de navegación persistida, tres diálogos, A/B, waveform sintética, entrega, reflow y contraste de tokens. No constituye auditoría integral WCAG ni aceptación amateur. S06-01 sigue parcial: falta restauración de paneles abiertos como preferencias UI prevista por el contrato, revisión integral de contraste de estados y cierre de accesibilidad. Próximo bloque de desarrollo: preferencias de paneles vinculadas al proyecto sin alterar MusicSpec.

El intento anterior de MCP no se ejecutó por límite de aprobación automática; los resultados de este reporte corresponden al reintento ejecutado.

## Actualización de accesibilidad

Paneles abiertos ya persisten por proyecto y su recarga/aislamiento se comprobó con Alma e Isabella en DB QA. Nombres A/B/sample y aria-busy implementados. Playwright: movimiento reducido y 320 px comprobados; contraste exploratorio 999 elementos sin incidencias en fondos computados. Pendientes concretos: zoom/texto 200%, contraste condicional completo y tecnología asistiva/aceptación. No certificación WCAG.

## Texto ampliado

Simulación de texto 200% a 768 px en cinco pantallas sin overflow horizontal. Riesgo de footer fijo corregido mediante ResizeObserver, padding/scroll-padding dinámicos y altura máxima 50vh. Ensayo final: 335/367/359 px footer/reserva/scroll-padding. No equivale a zoom nativo ni lector de pantalla.
