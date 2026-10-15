# S01: alinear producción con sample opcional

## Entrega

- `FinalProductionGate` comprueba vínculo al set SQLite, sus tres assets y ficha válida confirmada. No consulta samples.
- Rutas locales de full-song, mastering, exportación y descarga final usan esta política compartida. El entry point histórico de `SampleGate.require_for_project` delega a la misma política para mantener compatibilidad.
- `SampleGate.require_for_set` conserva la comprobación explícita de evidencia del sample: vigencia, checksum, señal y limitaciones de procedencia real. No acredita calidad ni bloquea generar completo.
- La ruta ACE-Step conserva aprobación del plan/request, validación de fuentes y preflight. Eliminar el requisito de sample no aprueba un request automáticamente.
- Mensajes de UI y asistencia explican la opción. La procedencia de un provider ya no se anuncia como calidad audible aprobada.
- Corregida preparación de letras antiguas sin ID: asignación estable por posición, sin colisiones con IDs existentes, texto y originales preservados, transformación trazada y ficha pendiente. No se reseedean proyectos existentes.

## Verificación agrupada

90 casos backend ejecutados: 85 aprobados, 5 omitidos. Incluye exportación histórica, candidatos, samples, comandos locales, preparación/concurrencia y recomendaciones. Los casos de letra del workflow histórico llaman explícitamente al servicio histórico conservado; las rutas modernas siguen propuestas revisables sin autoguardado. Las expectativas de preparación desde set ahora exigen ausencia de aprobación automática y de reseeding durante listado.

La primera corrida detectó un fallo de snapshot por sección sin ID y expectativas antiguas. Tras corregirlos, el lote terminó OK. La regresión final adicional aprobó 27 casos, incluido el caso nuevo de IDs faltantes y colisiones; estos casos se solapan con el lote y no se suman como cobertura única.

52 pruebas frontend aprobadas, build Vite aprobado, compileall aprobado y diff check sin errores (avisos de conversión LF/CRLF). Sin nueva generación musical ni nuevas pruebas con modelos cargados. Este bloque no acredita escucha, aceptación final ni piloto amateur. La API que estaba en ejecución requiere reinicio para cargar cambios backend.

## Balance

S01-01 ya figuraba D=1/V=1: se corrige su evidencia y pendiente, sin sumar avance duplicado. S00-04 V=0→0.5 y S10-01 V=0→0.5 reconocen la ejecución real Turbo/direct/XPU de Isabella, sus comprobaciones técnicas y feedback persistido. Permanecen pendientes otros checkpoints/rutas, escucha completa, fidelidad y aceptación; voz sintética reportada alrededor de 20 s. La corrección musical se aplaza por solicitud del usuario.
