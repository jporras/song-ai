# S00 — Contrato completo de inputs en la frontera del wrapper

## Entrega

Antes solo cuatro opciones (`seed`, pasos, guidance y shift) se cotejaban con el contexto de ejecución. Ahora `AceStepExecutionArguments` exporta todos los inputs del payload aprobado a `ace_execution_context.json`, junto a revisión/hash y checksums verificados de fuente/referencia. No crea otra fuente activa: es un snapshot del plan SQLite para ejecutar.

El CLI lee caption/letra y coteja los 21 nombres conectados con `runtime_input_trace`, además del perfil/opciones con `runtime_trace`, antes de crear directorios de modelo, borrar un output previo o cargar pesos. Fuentes con evidencia aprobada se vuelven a comprobar por SHA256. Un valor o archivo distinto bloquea la ejecución, sin redondear, truncar o corregir decisiones.

Diagnóstico incluye entradas de valor aprobado → valor leído, revisión/hash y checksums cotejados. Aliases MusicSpec/USER → payload siguen documentados en `input_trace` del plan; el nuevo tramo payload → CLI declara identidad, sin atribuir un alias de idioma/compás al motor. Mantiene separación entre petición, argumentos efectivos y observación/calidad del resultado.

Contextos antiguos o llamadas manuales sin `approved_inputs` siguen funcionando con estado `legacy_context_without_full_input_contract`; no se presentan como comprobación completa. La comparación depende del contexto exportado por la aplicación, no es autenticación criptográfica frente a modificación simultánea de CLI/contexto por un tercero. Las rutas de aplicación conservan revisión, aprobación/hash y revalidación del plan.

## Verificación agrupada

41 pruebas aprobadas: inputs/runtime options, aceptación USER, ejecución, compilador, alto nivel, aprobación del plan, candidatos y evidencia de runtime. Se verifican:

- Los 21 campos tienen regla y se preservan; cada alteración no autorizada se rechaza.
- Caption y letra con acentos llegan sin modificación.
- Archivo seleccionado conserva SHA256 y una sustitución se rechaza.
- Contexto mal formado, input desconocido, revisión ausente y checksum inválido se rechazan.
- Contexto de trece combinaciones de tareas/API compatibles conserva payload aprobado completo.
- CLI real con BPM cambiado rechaza antes de diagnóstico/modelos y conserva el output anterior. No carga torch ni ACE-Step.

No se hizo nueva generación ni prueba de todas las pantallas. S00-03 D=0.5→1, V=0.5 y A=0 se conservan: matriz integral UI/chat/persistencia, controles condicionales y aceptación siguen pendientes. No se modifica la aprobación de Isabella ni sus archivos.
