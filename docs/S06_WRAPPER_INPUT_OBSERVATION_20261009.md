# S06: vinculo entre plan y observacion del wrapper — 2026-10-09

## Correccion

read_candidate_runtime descartaba runtime_input_trace. Ahora lo conserva en runtime_evidence del artefacto/task SQLite y compara con el plan aprobado mediante adapter puro ace_step_input_observation. Verifica revision, hash, conjunto completo de campos sin duplicados, valores aprobados/observados, transformacion identity y checksums fuente/referencia. El scope declara wrapper, no motor ni calidad.

El runner local de nuevas generaciones exige observacion matched antes de retornar candidato. Diagnostico ausente/malformado o incompatible no acredita inputs; se informa fallo y no se registra candidato como resultado aceptable. Archivos/eventos de fallo siguen disponibles para diagnostico. No se modifican artefactos ni opiniones historicas. Lector historico sin plan devuelve plan_not_compared; traza ausente devuelve unavailable, nunca coincidencia inferida.

## Evidencia

22 pruebas del lote aprobadas: observacion, diagnosticos, candidatos, construccion de argumentos, CLI/input guard y contrato USER. Mutaciones de revision/hash/valores/transformacion/checksum/cobertura rechazadas; runner rechaza ausencia/discrepancia. WAV tecnico y mocks del proceso, no inferencia nueva. No atribuir carga, ejecucion nativa ni fidelidad audible a estas pruebas.

S06-05 continua V0.5: falta observar parametros efectivos del motor real y mapping restante de direccion por seccion. S00-04 carga por rutas sigue pendiente; avance D/V89.4%. Isabella conserva aceptacion original, sin regeneracion ni nueva evidencia atribuida retroactivamente.
