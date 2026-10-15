# Pendientes para cerrar el sprint — corte 2026-10-15

Fuente de estado: `sprint_progress.json`, generado en `SPRINT_PROGRESS.md`. Alcance activo S00–S06 y S10: desarrollo 100 %, verificación parcial en cinco entregables, avance D/V 97,9 %. Este documento es un handoff de trabajo, no una aprobación del audio.

## Verificación técnica pendiente

| ID | Qué falta demostrar | Prueba de salida |
| --- | --- | --- |
| S00-04 | Carga, configuración y uso efectivo del LM opcional de ACE-Step. | Job QA `high_level_lm` completado con checkpoint identificado, configuración efectiva observada y artefacto ligado a plan/revisión. La ruta alto nivel sin LM no cubre esto. |
| S01-04 | Cierre y descarga integrada del resultado real. | Resultado final real con artefactos exportables exigidos por el servicio, integridad por checksum, manifest/ZIP y descarga desde el proyecto; la descarga aislada del WAV de candidato ya está comprobada. |
| S06-05 | Parámetros efectivos observados dentro del motor y límites de traducción de dirección por sección. | Cotejo plan → request → wrapper → informe del motor, con cada campo traducido o límite declarado. La traza del wrapper por sí sola sigue siendo parcial. |
| S06-06 | Feedback, corrección y segundo resultado con audio real. | Recorrido QA persistido y reabierto con revisión vigente, plan corregido, dos candidatos reales y trazabilidad de artefactos. Las pruebas con WAV sintético ya existen. No registrar una escucha humana que no haya ocurrido. |
| S10-07 | Recorrido integrado idea → set válido → request confirmado → corrección → entrega real. | UI/backend/SQLite con proyecto QA aislado, segundo resultado real, descarga y conservación del original; sin atribuir decisiones creativas QA al usuario. |

La prueba LM1.7B quedó detenida por preflight: 9561 MB de pesos + 2048 MB de reserva = **11609 MB** requeridos, frente a **10540 MB** disponibles en la medición del preflight. La medición posterior fue 10031 MB. Antes de cargar ACE-Step, volver a medir RAM y cumplir el presupuesto completo; no reducir el gate ni cambiar a un checkpoint incompleto para forzar un resultado. Seis modos reales previos y la ruta de alto nivel sin LM conservan sus evidencias y no se regeneran por rutina.

## Aceptación posterior al 100 % D/V

- Escuchar completos los candidatos Cover, Repaint, Lego, Extract y Complete y comparar con sus fuentes según `PENDING_AUDIO_LISTENING_20261015.md`.
- Evaluar por oído el sample opcional de `REAL_SAMPLE_CORRESPONDENCE_20261015.md`, la preferencia A/B y el resultado final; registrar decisión, revisión y checksum. La correspondencia técnica del sample no acredita calidad audible.
- Recorrer la interfaz con personas sin experiencia musical según `AMATEUR_PILOT_PROTOCOL.md`; registrar resultados y defectos. Ningún piloto consta ejecutado.

## Evidencia ya obtenida y orden al retomar

Nivel P: 370 pruebas Python (365 aprobadas, 5 omitidas), 63 frontend aprobadas, build Vite y compilación correctos. Nivel L: Gemma y Qwen reales respondieron con steering en QA; no se guardaron propuestas como USER. Nivel A: seis modos reales anteriores, sample real opcional técnicamente cotejado, sin LM opcional nuevo. Detalle y límites en `SPRINT_VERIFICATION_BATCH_20261015.md` y `VERIFICATION_STRATEGY.md`.

Reanudar primero los casos independientes de exportación e integración con QA aislada; luego, cuando el preflight lo permita, observar LM y parámetros nativos en un lote ACE-Step serializado. Actualizar el ledger solo cuando la evidencia cubra la prueba de salida de cada ID. Después de D/V 100 %, realizar la aceptación.
