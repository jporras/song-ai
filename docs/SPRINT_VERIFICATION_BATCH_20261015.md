# Continuación de verificación por complejidad — 2026-10-15

Estado al inicio del lote: desarrollo 100%; seis entregables con verificación técnica parcial. S01-03 se cerró técnicamente más adelante en este mismo lote; quedan cinco. La aceptación musical y el piloto del usuario se harán al terminar D/V. Orden y criterios: `VERIFICATION_STRATEGY.md`, sección «Lotes por complejidad». Se conserva toda evidencia real anterior que sigue aplicando; no se repiten seis generaciones por rutina.

| Nivel | Resultado de esta ejecución | Alcance acreditado |
| --- | --- | --- |
| P — Python e interfaz sin modelos | `python -m unittest discover -s tests -p 'test_*.py' -q`: 370 ejecutadas, 365 aprobadas, 5 omitidas, 0 fallidas, 108,986 s. `node --test frontend/tests/*.test.js`: 63 aprobadas, 0 fallidas. `npx vite build --configLoader runner`: 40 módulos, build correcto. `python -m compileall -q backend scripts tools`: correcto. `python tools/check_acestep_contract.py`: compatible, 0 problemas; modelo no cargado/audio no generado. | Fixtures de audio fuente y recursos corregidas en la continuación anterior, ahora con suite completa aprobada. Contrato instalado estático, no ejecución nativa ni inferencia. El cargador predeterminado de Vite encontró antes un error de acceso del entorno; runner compiló la misma aplicación. |
| L — Gemma/Qwen reales | Gemma y Qwen respondieron por registry con steering el 15 de octubre; detalles y límites en la continuación de este documento. Se conserva también `REAL_TEXT_MODEL_BATCH_20261009.md` y `QWEN_STARTUP_PROFILE_FIX_20261009.md`. | Probes reales sin task nueva ni guardado; la revisión larga persistida corresponde a la evidencia anterior. Los servidores se cerraron y se comprobó la liberación de RAM. |
| A — ACE-Step real | No se inició nueva inferencia/audio. Se conservan seis modos reales, alto nivel sin LM, cancelación y descargas ya documentados. Preflight estático compatible, sin carga. Se creó un sample pendiente desde un WAV real existente y se verificó su correspondencia técnica. | El preflight de LM1.7B exigió 11609 MB frente a 10540 MB disponibles. La ruta LM opcional y parámetros nativos efectivos siguen sin observarse; el sample no tiene aprobación audible. |

## Pendientes técnicos sin nueva puntuación

- S00-04: carga, configuración y uso efectivo del LM opcional con request QA explícito.
- S01-03 se cerró técnicamente más adelante en este lote con correspondencia de sample real; su escucha/aceptación va después.
- S01-04: cierre y descarga final integrados de un resultado real, incluidos exportables verificados; la descarga WAV de candidato real ya está documentada.
- S06-05: parámetros reportados por el motor, aparte de la observación del wrapper; mapping de dirección que sea realmente ejecutable.
- S06-06: feedback, corrección, segundo resultado real, persistencia y recarga; el mismo recorrido con WAV sintético ya está documentado.
- S10-07: idea hasta entrega real con corrección, sin reutilizar una aprobación creativa ajena del escenario QA.

Este registro inicial correspondía al estado tras el bloque P. La continuación L/A y el nuevo estado de S01-03 se detallan abajo. Para reanudar ACE-Step con LM, medir de nuevo y cumplir el presupuesto completo de pesos y reserva, además del mínimo general de 3500 MB. Si el preflight falla, no lanzar pesos. La aceptación del usuario permanece separada.

## Continuación con memoria liberada — 2026-10-15

La RAM disponible subió a 8132 MB, swap 0. Se iniciaron Gemma y Qwen con `start-local-llms.ps1` y perfiles existentes; ambos `/health` respondieron 200. Desde el registry con steering completo se leyó MusicSpec de Alma de SQLite QA en modo solo lectura. No se escribió ni aprobó ninguna propuesta:

| Rol | Inferencia observada | Límite |
| --- | --- | --- |
| Gemma | `mode=llama_cpp`; 18,75 s; steering revision `f05823d42afb2f33e2134e0d0a05c113abcfb7efb1acddad2ce2e90a76e0b681`; pidió confirmar letra/intenciones antes de continuar. | Probe breve, no ensayo de obediencia universal ni task persistida nueva. |
| Qwen | `mode=llama_cpp`; 50,42 s; steering revision `ac7c09b7b09b3d7df6e992c13523cfc24d568a5d202f47c173e17faedae8fd69`; emitió propuesta técnica con campos pendientes. | No se guardó como deseo USER ni se atribuyó aprobación creativa. El probe no repite la revisión larga histórica. |

La carga conjunta redujo RAM disponible a ~301 MB. `stop-local-llms.ps1` recibió acceso denegado de CIM en este shell administrado. Se cerraron únicamente los PID 8644/13804 iniciados en esta continuación, después de cotejar PID registrados y ruta exacta del ejecutable; RAM disponible posterior 10743 MB. El script de cierre ahora tiene fallback seguro para CIM denegado: exige PID fresco, nombre, ruta y hora de proceso; rechazo si difieren. Sin PID, comprueba los puertos configurados y bloquea si alguno sigue abierto. Seis escenarios PowerShell aprobados: cierre normal, fallback válido, ejecutable ajeno, PID antiguo, puertos cerrados sin PID y puerto abierto sin PID. El script real volvió a salir 0 tras el cierre manual y retiró registros obsoletos. Esto mejora el handoff sin atribuir un nuevo punto al ledger.

Preflight ACE-Step sin cargar pesos: Turbo + `high_level_lm` + LM1.7B, ruta única local completa. `estimate_ace_step_memory` **sí** incorpora el LM: 9561 MB de pesos y 2048 MB de reserva, total requerido **11609 MB**. RAM medida **10540 MB**; `passes_memory_gate=false`. Informe `data/runtime/ace_lm_preflight_20261015.json`. No se inició un job, no se sustituyó por LM0.6B (incompleto) ni se acreditó S00-04/S06-05. Para continuar esta ruta faltan al menos 1069 MB de RAM disponible adicional al momento del preflight y margen para variaciones; no cerrar otras aplicaciones automáticamente.

## S01-03: sample real opcional con correspondencia técnica

Se creó un sample pendiente desde el candidato ACE-Step real de la QA alto nivel y se evaluó/reabrió en SQLite: set, plan, revisión, checksum y ejecución/configuración coinciden. `configuration_matches=true`, `execution_configuration_matches=true`, `assessment_current=true`; `representativity_verified=false` y `approval_status=pending`. Evidencia exacta en `REAL_SAMPLE_CORRESPONDENCE_20261015.md`. S01-03 cambia V0.5→1 para esta correspondencia técnica; la escucha y representatividad perceptual quedan en aceptación. No se generó audio adicional ni se volvió obligatorio el sample.
